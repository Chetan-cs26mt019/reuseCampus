import pytest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Category, Enquiry, EnquiryMessage, Listing, User
from app.services.enquiries import (
    create_enquiry,
    get_enquiry_for_participant,
    list_enquiry_messages,
    send_enquiry_message,
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
def setup_users_and_listing(db):
    seller = User(
        email="seller@example.test",
        username="seller",
        password_hash="test-hash",
        full_name="Seller",
    )
    buyer = User(
        email="buyer@example.test",
        username="buyer",
        password_hash="test-hash",
        full_name="Buyer",
    )
    outsider = User(
        email="outsider@example.test",
        username="outsider",
        password_hash="test-hash",
        full_name="Outsider",
    )
    category = Category(name="Books")

    db.add_all([seller, buyer, outsider, category])
    db.flush()

    listing = Listing(
        seller_id=seller.id,
        category_id=category.id,
        title="Algorithms textbook",
        description="Used textbook",
        price=300,
        condition="good",
        status="available",
    )

    db.add(listing)
    db.commit()

    return seller, buyer, outsider, listing


def test_create_enquiry(db, setup_users_and_listing):
    seller, buyer, _, listing = setup_users_and_listing

    enquiry = create_enquiry(db, buyer, listing.id)

    assert enquiry.status == "open"
    assert enquiry.buyer_id == buyer.id
    assert enquiry.seller_id == seller.id


def test_cannot_enquire_about_own_listing(
    db, setup_users_and_listing
):
    seller, _, _, listing = setup_users_and_listing

    with pytest.raises(HTTPException) as error:
        create_enquiry(db, seller, listing.id)

    assert error.value.status_code == 400


def test_outsider_cannot_view_enquiry(
    db, setup_users_and_listing
):
    _, buyer, outsider, listing = setup_users_and_listing
    enquiry = create_enquiry(db, buyer, listing.id)

    with pytest.raises(HTTPException) as error:
        get_enquiry_for_participant(db, outsider, enquiry.id)

    assert error.value.status_code == 404


def test_only_participants_can_read_messages(
    db, setup_users_and_listing
):
    _, buyer, outsider, listing = setup_users_and_listing
    enquiry = create_enquiry(db, buyer, listing.id)

    db.add(
        EnquiryMessage(
            enquiry_id=enquiry.id,
            sender_id=buyer.id,
            body="Is this book available?",
        )
    )
    db.commit()

    messages = list_enquiry_messages(db, buyer, enquiry.id)
    assert len(messages) == 1
    assert messages[0].body == "Is this book available?"

    with pytest.raises(HTTPException) as error:
        list_enquiry_messages(db, outsider, enquiry.id)

    assert error.value.status_code == 404


def test_message_sender_is_authenticated_user(
    db, setup_users_and_listing
):
    _, buyer, outsider, listing = setup_users_and_listing
    enquiry = create_enquiry(db, buyer, listing.id)

    message = send_enquiry_message(
        db, buyer, enquiry.id, "Hello, is this available?"
    )

    assert message.sender_id == buyer.id
    assert message.enquiry_id == enquiry.id

    with pytest.raises(HTTPException) as error:
        send_enquiry_message(
            db, outsider, enquiry.id, "Unauthorized message"
        )

    assert error.value.status_code == 404