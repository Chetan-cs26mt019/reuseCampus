import pytest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Category, Listing, User
from app.services.marketplace import (
    create_listing,
    get_listing,
    list_categories,
    search_listings,
    update_listing,
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
def marketplace_data(db):
    seller = User(
        email="seller-market@example.test",
        username="seller_market",
        password_hash="test-hash",
        full_name="Seller",
    )
    outsider = User(
        email="outsider-market@example.test",
        username="outsider_market",
        password_hash="test-hash",
        full_name="Outsider",
    )
    books = Category(name="Books")
    electronics = Category(name="Electronics")
    inactive = Category(name="Inactive", is_active=False)

    db.add_all([seller, outsider, books, electronics, inactive])
    db.flush()

    listing = Listing(
        seller_id=seller.id,
        category_id=books.id,
        title="Python Textbook",
        description="A useful programming book",
        price=250,
        condition="good",
        status="available",
    )
    hidden = Listing(
        seller_id=seller.id,
        category_id=books.id,
        title="Hidden Book",
        description="Not publicly visible",
        price=100,
        condition="used",
        status="available",
        hidden_at=None,
    )
    unavailable = Listing(
        seller_id=seller.id,
        category_id=electronics.id,
        title="Reserved Laptop",
        description="Currently reserved",
        price=15000,
        condition="good",
        status="reserved",
    )

    db.add_all([listing, hidden, unavailable])
    db.commit()

    return seller, outsider, books, electronics, inactive, listing, unavailable


def test_only_active_categories_are_listed(db, marketplace_data):
    categories = list_categories(db)

    assert [category.name for category in categories] == [
        "Books",
        "Electronics",
    ]


def test_create_listing_success(db, marketplace_data):
    seller, _, books, _, _, _, _ = marketplace_data

    listing = create_listing(
        db,
        seller,
        category_id=books.id,
        title="  New Book  ",
        description="  A clear description  ",
        price=Decimal("99.50"),
        condition=" good ",
    )

    assert listing.seller_id == seller.id
    assert listing.title == "New Book"
    assert listing.description == "A clear description"
    assert listing.condition == "good"
    assert listing.status == "available"
    assert listing.currency == "INR"


def test_cannot_create_listing_in_inactive_category(db, marketplace_data):
    seller, _, _, _, inactive, _, _ = marketplace_data

    with pytest.raises(HTTPException) as error:
        create_listing(
            db,
            seller,
            category_id=inactive.id,
            title="New Book",
            description="Description",
            price=Decimal("10.00"),
            condition="good",
        )

    assert error.value.status_code == 422


def test_search_by_keyword_and_category(db, marketplace_data):
    _, _, books, _, _, listing, _ = marketplace_data

    results = search_listings(
        db,
        q="Python",
        category_id=books.id,
    )

    assert [item.id for item in results] == [listing.id]


def test_search_by_price_range(db, marketplace_data):
    _, _, _, _, _, listing, _ = marketplace_data

    results = search_listings(
        db,
        min_price=Decimal("200"),
        max_price=Decimal("300"),
    )

    assert [item.id for item in results] == [listing.id]


def test_search_excludes_unavailable_listings(db, marketplace_data):
    _, _, _, _, _, listing, _ = marketplace_data

    results = search_listings(db)

    assert listing.id in [item.id for item in results]
    assert all(item.status == "available" for item in results)


def test_search_rejects_invalid_price_range(db):
    with pytest.raises(HTTPException) as error:
        search_listings(
            db,
            min_price=Decimal("500"),
            max_price=Decimal("100"),
        )

    assert error.value.status_code == 422


def test_listing_owner_can_update(db, marketplace_data):
    seller, _, books, _, _, listing, _ = marketplace_data

    updated = update_listing(
        db,
        seller,
        listing.id,
        {"title": "Updated Python Book", "category_id": books.id},
    )

    assert updated.title == "Updated Python Book"


def test_other_user_cannot_update_listing(db, marketplace_data):
    _, outsider, _, _, _, listing, _ = marketplace_data

    with pytest.raises(HTTPException) as error:
        update_listing(
            db,
            outsider,
            listing.id,
            {"title": "Not my listing"},
        )

    assert error.value.status_code == 403


def test_missing_listing_returns_404(db):
    with pytest.raises(HTTPException) as error:
        get_listing(db, 999999)

    assert error.value.status_code == 404


from decimal import Decimal


def test_add_favourite(db, marketplace_data):
    from app.models import Favourite
    from app.services.marketplace import add_favourite

    seller, _, _, _, _, listing, _ = marketplace_data

    result = add_favourite(db, seller, listing.id)

    assert result.id == listing.id
    assert db.get(Favourite, (seller.id, listing.id)) is not None


def test_add_favourite_twice_does_not_duplicate(db, marketplace_data):
    from app.models import Favourite
    from app.services.marketplace import add_favourite

    seller, _, _, _, _, listing, _ = marketplace_data

    add_favourite(db, seller, listing.id)
    add_favourite(db, seller, listing.id)

    favourites = db.query(Favourite).filter_by(
        user_id=seller.id,
        listing_id=listing.id,
    ).all()

    assert len(favourites) == 1


def test_remove_favourite(db, marketplace_data):
    from app.services.marketplace import add_favourite, remove_favourite
    from app.models import Favourite

    seller, _, _, _, _, listing, _ = marketplace_data

    add_favourite(db, seller, listing.id)
    remove_favourite(db, seller, listing.id)

    assert db.get(Favourite, (seller.id, listing.id)) is None


def test_cannot_remove_another_users_favourite(db, marketplace_data):
    from app.services.marketplace import add_favourite, remove_favourite

    seller, outsider, _, _, _, listing, _ = marketplace_data

    add_favourite(db, seller, listing.id)

    with pytest.raises(HTTPException) as error:
        remove_favourite(db, outsider, listing.id)

    assert error.value.status_code == 404


def test_list_favourites_only_returns_users_own(db, marketplace_data):
    from app.services.marketplace import add_favourite, list_favourites

    seller, outsider, _, _, _, listing, _ = marketplace_data

    add_favourite(db, seller, listing.id)

    assert [item.id for item in list_favourites(db, seller)] == [listing.id]
    assert list_favourites(db, outsider) == []


def test_cannot_favourite_unavailable_listing(db, marketplace_data):
    from app.services.marketplace import add_favourite

    seller, _, _, _, _, _, unavailable = marketplace_data

    with pytest.raises(HTTPException) as error:
        add_favourite(db, seller, unavailable.id)

    assert error.value.status_code == 404
