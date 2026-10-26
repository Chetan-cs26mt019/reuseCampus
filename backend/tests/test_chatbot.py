import pytest

from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Category, Listing
from app.services.chatbot import (
    create_guest_session,
    process_chat_message,
)
from datetime import timedelta

from sqlalchemy import select

from app.models import ChatMessage, ChatFeedback
from app.services import chatbot
from app.services.chatbot import create_chat_feedback


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
def chat_setup(db):
    category = Category(name="Books")
    db.add(category)
    db.flush()

    # A minimal seller is required by the listing foreign key.
    from app.models import User

    seller = User(
        email="seller@example.test",
        username="seller",
        password_hash="test-hash",
        full_name="Test Seller",
    )
    db.add(seller)
    db.flush()

    book = Listing(
        seller_id=seller.id,
        category_id=category.id,
        title="Algorithms Textbook",
        description="A used computer science book",
        price=Decimal("400.00"),
        currency="INR",
        condition="good",
        status="available",
    )

    hidden_book = Listing(
        seller_id=seller.id,
        category_id=category.id,
        title="Hidden Algorithms Book",
        description="A hidden book",
        price=Decimal("100.00"),
        currency="INR",
        condition="good",
        status="hidden",
    )

    db.add_all([book, hidden_book])
    db.commit()

    session, token = create_guest_session(db)

    return session, token, book, hidden_book


from decimal import Decimal


def test_create_guest_session(db):
    session, token = create_guest_session(db)

    assert session.id is not None
    assert token
    assert session.guest_token_hash != token


def test_search_returns_available_listing(
    db, chat_setup
):
    session, token, book, _ = chat_setup

    result = process_chat_message(
        db,
        session.id,
        token,
        "books",
    )

    assert result["result_count"] == 1
    assert result["listings"][0]["listing_id"] == book.id
    assert result["listings"][0]["title"] == "Algorithms Textbook"


def test_price_limit_is_applied(db, chat_setup):
    session, token, book, _ = chat_setup

    result = process_chat_message(
        db,
        session.id,
        token,
        "books under 500",
    )

    assert result["result_count"] == 1
    assert result["listings"][0]["listing_id"] == book.id


def test_invalid_guest_token_is_rejected(
    db, chat_setup
):
    session, _, _, _ = chat_setup

    with pytest.raises(HTTPException) as error:
        process_chat_message(
            db,
            session.id,
            "incorrect-token",
            "books",
        )

    assert error.value.status_code == 404


def test_hidden_listings_are_not_returned(
    db, chat_setup
):
    session, token, _, hidden_book = chat_setup

    result = process_chat_message(
        db,
        session.id,
        token,
        "hidden",
    )

    assert all(
        item["listing_id"] != hidden_book.id
        for item in result["listings"]
    )


def test_empty_message_is_rejected(db, chat_setup):
    session, token, _, _ = chat_setup

    with pytest.raises(HTTPException) as error:
        process_chat_message(
            db,
            session.id,
            token,
            "   ",
        )

    assert error.value.status_code == 422

def test_guest_rate_limit_allows_ten_messages(db, chat_setup):
    session, token, _, _ = chat_setup

    # Reset shared in-memory state so this test is isolated.
    with chatbot._rate_limit_lock:
        chatbot._message_timestamps.clear()

    try:
        for _ in range(10):
            result = chatbot.process_chat_message(
                db, session.id, token, "books"
            )
            assert result["result_count"] == 1

        with pytest.raises(HTTPException) as error:
            chatbot.process_chat_message(
                db, session.id, token, "books"
            )

        assert error.value.status_code == 429
        assert error.value.headers["Retry-After"] == "60"
    finally:
        with chatbot._rate_limit_lock:
            chatbot._message_timestamps.clear()


def test_expired_guest_session_is_rejected(db, chat_setup):
    session, token, _, _ = chat_setup

    session.expires_at = chatbot._utcnow() - timedelta(minutes=1)
    db.commit()

    with pytest.raises(HTTPException) as error:
        chatbot.process_chat_message(
            db, session.id, token, "books"
        )

    assert error.value.status_code == 401


def test_feedback_can_be_saved_for_assistant_message(db, chat_setup):
    session, token, _, _ = chat_setup

    chatbot.process_chat_message(
        db, session.id, token, "books"
    )

    assistant_message = db.scalar(
        select(ChatMessage).where(
            ChatMessage.session_id == session.id,
            ChatMessage.role == "assistant",
        )
    )
    assert assistant_message is not None

    result = create_chat_feedback(
        db=db,
        session_id=session.id,
        token=token,
        rating="helpful",
        message_id=assistant_message.id,
        comments="Useful results",
    )

    assert result["session_id"] == session.id
    assert result["message_id"] == assistant_message.id
    assert result["rating"] == "helpful"
    assert result["comments"] == "Useful results"


def test_feedback_cannot_reference_another_sessions_message(
    db, chat_setup
):
    session, token, _, _ = chat_setup
    other_session, other_token = create_guest_session(db)

    chatbot.process_chat_message(
        db, other_session.id, other_token, "books"
    )

    other_message = db.scalar(
        select(ChatMessage).where(
            ChatMessage.session_id == other_session.id,
            ChatMessage.role == "assistant",
        )
    )
    assert other_message is not None

    with pytest.raises(HTTPException) as error:
        create_chat_feedback(
            db=db,
            session_id=session.id,
            token=token,
            rating="helpful",
            message_id=other_message.id,
        )

    assert error.value.status_code == 404


def test_invalid_feedback_rating_is_rejected(db, chat_setup):
    session, token, _, _ = chat_setup

    with pytest.raises(HTTPException) as error:
        create_chat_feedback(
            db=db,
            session_id=session.id,
            token=token,
            rating="excellent",
        )

    assert error.value.status_code == 422