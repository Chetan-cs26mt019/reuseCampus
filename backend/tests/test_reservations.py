import pytest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Category, Listing, Reservation, User
from app.services.reservations import (
    change_reservation_status,
    create_reservation,
)


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
def people_and_listing(db):
    seller = User(
        email="seller@example.test",
        username="seller",
        password_hash="test-hash",
        full_name="Test Seller",
    )

    buyer = User(
        email="buyer@example.test",
        username="buyer",
        password_hash="test-hash",
        full_name="Test Buyer",
    )

    outsider = User(
        email="outsider@example.test",
        username="outsider",
        password_hash="test-hash",
        full_name="Test Outsider",
    )

    category = Category(name="Books")

    db.add_all([seller, buyer, outsider, category])
    db.flush()

    listing = Listing(
        seller_id=seller.id,
        category_id=category.id,
        title="Used textbook",
        description="A textbook in good condition",
        price=250.00,
        condition="good",
        status="available",
    )

    db.add(listing)
    db.commit()

    return seller, buyer, outsider, listing


def test_create_reservation_success(db, people_and_listing):
    seller, buyer, _, listing = people_and_listing

    reservation = create_reservation(db, buyer, listing.id)

    assert reservation.status == "requested"
    assert reservation.buyer_id == buyer.id
    assert reservation.seller_id == seller.id
    assert reservation.listing_id == listing.id
    assert listing.status == "reserved"


def test_cannot_reserve_own_listing(db, people_and_listing):
    seller, _, _, listing = people_and_listing

    with pytest.raises(HTTPException) as error:
        create_reservation(db, seller, listing.id)

    assert error.value.status_code == 400


def test_listing_cannot_have_two_active_reservations(
    db, people_and_listing
):
    _, buyer, outsider, listing = people_and_listing

    create_reservation(db, buyer, listing.id)

    with pytest.raises(HTTPException) as error:
        create_reservation(db, outsider, listing.id)

    assert error.value.status_code == 409


def test_seller_can_reject_and_release_listing(
    db, people_and_listing
):
    seller, buyer, _, listing = people_and_listing

    reservation = create_reservation(db, buyer, listing.id)

    result = change_reservation_status(
        db, seller, reservation.id, "reject"
    )

    assert result.status == "rejected"
    db.refresh(listing)
    assert listing.status == "available"


def test_buyer_can_cancel_and_release_listing(
    db, people_and_listing
):
    _, buyer, _, listing = people_and_listing

    reservation = create_reservation(db, buyer, listing.id)

    result = change_reservation_status(
        db, buyer, reservation.id, "cancel"
    )

    assert result.status == "cancelled"
    db.refresh(listing)
    assert listing.status == "available"


def test_only_seller_can_accept(db, people_and_listing):
    _, buyer, outsider, listing = people_and_listing

    reservation = create_reservation(db, buyer, listing.id)

    with pytest.raises(HTTPException) as error:
        change_reservation_status(
            db, outsider, reservation.id, "accept"
        )

    assert error.value.status_code == 403


def test_accept_and_complete_reservation(
    db, people_and_listing
):
    seller, buyer, _, listing = people_and_listing

    reservation = create_reservation(db, buyer, listing.id)

    accepted = change_reservation_status(
        db, seller, reservation.id, "accept"
    )

    assert accepted.status == "accepted"

    completed = change_reservation_status(
        db, buyer, reservation.id, "complete"
    )

    assert completed.status == "completed"
    assert completed.completed_at is not None
    assert listing.status == "sold"


def test_outsider_cannot_change_reservation(
    db, people_and_listing
):
    _, buyer, outsider, listing = people_and_listing

    reservation = create_reservation(db, buyer, listing.id)

    with pytest.raises(HTTPException) as error:
        change_reservation_status(
            db, outsider, reservation.id, "cancel"
        )

    assert error.value.status_code == 403
    assert reservation.status == "requested"
