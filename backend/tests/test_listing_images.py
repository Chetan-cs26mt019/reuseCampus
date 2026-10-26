from io import BytesIO
from PIL import Image

import asyncio
import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import select

from app.models import ListingImage
from app.services import listing_images
from app.services.listing_images import (
    MAX_IMAGE_SIZE,
    delete_listing_image,
    list_listing_images,
    upload_listing_image,
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Category, Listing, User


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def marketplace_data(db):
    seller = User(
        email="seller-images@example.test",
        username="seller_images",
        password_hash="test-hash",
        full_name="Seller",
    )
    outsider = User(
        email="outsider-images@example.test",
        username="outsider_images",
        password_hash="test-hash",
        full_name="Outsider",
    )
    category = Category(name="Books")

    db.add_all([seller, outsider, category])
    db.flush()

    listing = Listing(
        seller_id=seller.id,
        category_id=category.id,
        title="Test Book",
        description="Book for image tests",
        price=100,
        condition="good",
        status="available",
    )

    db.add(listing)
    db.commit()

    return seller, outsider, category, None, None, listing, None


# A minimal PNG signature for testing the current signature-based validator.
def make_png_data():
    buffer = BytesIO()
    Image.new("RGB", (2, 2), (255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


PNG_DATA = make_png_data()


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    directory = tmp_path / "uploads" / "listings"
    monkeypatch.setattr(listing_images, "UPLOAD_DIR", directory)
    return directory


def make_upload(data, filename="test.png"):
    return UploadFile(
        filename=filename,
        file=BytesIO(data),
    )


def test_upload_image_success(db, marketplace_data, upload_dir):
    asyncio.run(_test_upload_image_success(db, marketplace_data, upload_dir))

async def _test_upload_image_success(db, marketplace_data, upload_dir):
    seller, _, _, _, _, listing, _ = marketplace_data

    image = await upload_listing_image(
        db,
        seller,
        listing.id,
        make_upload(PNG_DATA, filename="../../unsafe.png"),
        alt_text="  Front view  ",
    )

    assert image.listing_id == listing.id
    assert image.alt_text == "Front view"
    assert image.image_url.startswith("/uploads/listings/")
    assert image.image_url.endswith(".png")
    assert len(list(upload_dir.iterdir())) == 1
    assert (upload_dir / image.image_url.rsplit("/", 1)[1]).read_bytes() == PNG_DATA


def test_rejects_invalid_image_signature(db, marketplace_data, upload_dir):
    asyncio.run(_test_rejects_invalid_image_signature(db, marketplace_data, upload_dir))

async def _test_rejects_invalid_image_signature(db, marketplace_data, upload_dir):
    seller, _, _, _, _, listing, _ = marketplace_data

    with pytest.raises(HTTPException) as error:
        await upload_listing_image(
            db, seller, listing.id, make_upload(b"not an image")
        )

    assert error.value.status_code == 415
    assert not upload_dir.exists() or not any(upload_dir.iterdir())
    assert db.scalars(select(ListingImage)).all() == []


def test_rejects_empty_file(db, marketplace_data, upload_dir):
    asyncio.run(_test_rejects_empty_file(db, marketplace_data, upload_dir))

async def _test_rejects_empty_file(db, marketplace_data, upload_dir):
    seller, _, _, _, _, listing, _ = marketplace_data

    with pytest.raises(HTTPException) as error:
        await upload_listing_image(
            db, seller, listing.id, make_upload(b"")
        )

    assert error.value.status_code == 422
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_rejects_oversized_file(db, marketplace_data, upload_dir):
    asyncio.run(_test_rejects_oversized_file(db, marketplace_data, upload_dir))

async def _test_rejects_oversized_file(db, marketplace_data, upload_dir):
    seller, _, _, _, _, listing, _ = marketplace_data

    oversized_data = b"\x89PNG\r\n\x1a\n" + b"x" * MAX_IMAGE_SIZE

    with pytest.raises(HTTPException) as error:
        await upload_listing_image(
            db, seller, listing.id, make_upload(oversized_data)
        )

    assert error.value.status_code == 413
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_other_seller_cannot_upload_image(db, marketplace_data, upload_dir):
    asyncio.run(_test_other_seller_cannot_upload_image(db, marketplace_data, upload_dir))

async def _test_other_seller_cannot_upload_image(db, marketplace_data, upload_dir):
    _, outsider, _, _, _, listing, _ = marketplace_data

    with pytest.raises(HTTPException) as error:
        await upload_listing_image(
            db, outsider, listing.id, make_upload(PNG_DATA)
        )

    assert error.value.status_code == 403
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_list_images_in_position_order(db, marketplace_data, upload_dir):
    asyncio.run(_test_list_images_in_position_order(db, marketplace_data, upload_dir))

async def _test_list_images_in_position_order(db, marketplace_data, upload_dir):
    seller, _, _, _, _, listing, _ = marketplace_data

    first = await upload_listing_image(
        db, seller, listing.id, make_upload(PNG_DATA)
    )
    second = await upload_listing_image(
        db, seller, listing.id, make_upload(PNG_DATA)
    )

    images = list_listing_images(db, listing.id)

    assert [image.id for image in images] == [first.id, second.id]
    assert [image.position for image in images] == [0, 1]


def test_delete_image_removes_database_record_and_file(db, marketplace_data, upload_dir):
    asyncio.run(_test_delete_image_removes_database_record_and_file(db, marketplace_data, upload_dir))

async def _test_delete_image_removes_database_record_and_file(db, marketplace_data, upload_dir):
    seller, _, _, _, _, listing, _ = marketplace_data

    image = await upload_listing_image(
        db, seller, listing.id, make_upload(PNG_DATA)
    )
    disk_path = upload_dir / image.image_url.rsplit("/", 1)[1]

    assert disk_path.exists()

    delete_listing_image(db, seller, listing.id, image.id)

    assert db.get(ListingImage, image.id) is None
    assert not disk_path.exists()


def test_listing_cannot_have_more_than_five_images(db, marketplace_data, upload_dir):
    asyncio.run(_test_listing_cannot_have_more_than_five_images(db, marketplace_data, upload_dir))

async def _test_listing_cannot_have_more_than_five_images(db, marketplace_data, upload_dir):
    seller, _, _, _, _, listing, _ = marketplace_data

    for _ in range(5):
        await upload_listing_image(
            db, seller, listing.id, make_upload(PNG_DATA)
        )

    with pytest.raises(HTTPException) as error:
        await upload_listing_image(
            db, seller, listing.id, make_upload(PNG_DATA)
        )

    assert error.value.status_code == 409
    assert len(list(upload_dir.iterdir())) == 5
