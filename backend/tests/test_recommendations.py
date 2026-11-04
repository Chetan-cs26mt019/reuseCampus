import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import (
    AIEmbedding,
    Category,
    Favourite,
    Listing,
    User,
)
from app.services import recommendations as service


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def marketplace(db, monkeypatch):
    seller1 = User(
        email="seller1@test.local",
        username="seller1",
        password_hash="hash",
        full_name="Seller One",
    )
    seller2 = User(
        email="seller2@test.local",
        username="seller2",
        password_hash="hash",
        full_name="Seller Two",
    )
    buyer = User(
        email="buyer@test.local",
        username="buyer",
        password_hash="hash",
        full_name="Buyer",
    )
    books = Category(name="Books", is_active=True)
    electronics = Category(name="Electronics", is_active=True)
    db.add_all([seller1, seller2, buyer, books, electronics])
    db.flush()

    source = Listing(
        seller_id=seller1.id,
        category_id=books.id,
        title="Python Programming Book",
        description="Learn Python programming",
        price=200,
        condition="good",
        status="available",
    )
    same_seller = Listing(
        seller_id=seller1.id,
        category_id=books.id,
        title="Advanced Python Book",
        description="Advanced programming with Python",
        price=250,
        condition="good",
        status="available",
    )
    other_seller = Listing(
        seller_id=seller2.id,
        category_id=electronics.id,
        title="Scientific Calculator",
        description="Calculator for engineering students",
        price=300,
        condition="good",
        status="available",
    )
    db.add_all([source, same_seller, other_seller])
    db.commit()

    def fake_embedding(text):
        vector = [0.0] * 384
        text = text.lower()

        if "python" in text or "book" in text:
            vector[0] = 1.0
        else:
            vector[1] = 1.0

        return vector

    monkeypatch.setattr(service, "make_embedding", fake_embedding)

    return buyer, seller1, source, same_seller, other_seller


def test_similar_recommendations_include_same_seller_listings(db, marketplace):
    _, _, source, same_seller, other_seller = marketplace

    results = service.similar_recommendations(db, source.id)

    ids = [item["listing"].id for item in results]
    assert same_seller.id in ids
    assert source.id not in ids


def test_similar_recommendations_return_404_for_missing_listing(db):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        service.similar_recommendations(db, 99999)

    assert error.value.status_code == 404


def test_personalized_recommendations_use_favourites(db, marketplace):
    buyer, _, source, _, other_seller = marketplace

    db.add(Favourite(user_id=buyer.id, listing_id=source.id))
    db.commit()

    results = service.personalized_recommendations(db, buyer.id)

    assert results
    assert all(item["listing"].id != source.id for item in results)


def test_new_user_gets_popular_fallback(db, marketplace):
    buyer, _, _, _, _ = marketplace

    results = service.personalized_recommendations(db, buyer.id)

    assert results
    assert all(item["reason"] == "Popular among campus users" for item in results)


def test_embedding_is_cached(db, marketplace, monkeypatch):
    _, _, source, _, _ = marketplace
    calls = {"count": 0}
    original = service.make_embedding

    def counted_embedding(text):
        calls["count"] += 1
        return original(text)

    monkeypatch.setattr(service, "make_embedding", counted_embedding)

    first = service.get_listing_embedding(db, source)
    second = service.get_listing_embedding(db, source)

    assert first == second
    assert calls["count"] == 1
    assert db.query(AIEmbedding).filter_by(listing_id=source.id).count() == 1
