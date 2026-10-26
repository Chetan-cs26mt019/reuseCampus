import hashlib
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AIQuery,
    Category,
    ChatFeedback,
    ChatMessage,
    ChatSession,
    Listing,
    ListingImage,
)
from collections import defaultdict, deque
from threading import Lock


MAX_RESULTS = 5
SESSION_LIFETIME_HOURS = 24

STOP_WORDS = {
    "a", "an", "the", "i", "me", "my", "find", "show",
    "search", "looking", "for", "want", "need", "please",
    "under", "below", "less", "than", "price", "with",
    "available", "listings", "listing", "items", "item",
    "rs", "inr", "rupees", "₹", "cheap", "buy", "get",
}

MAX_MESSAGES_PER_MINUTE = 10
RATE_LIMIT_WINDOW_SECONDS = 60

_message_timestamps = defaultdict(deque)
_rate_limit_lock = Lock()


def _check_message_rate_limit(session_id: int) -> None:
    """Allow at most 10 messages per session in a rolling 60-second window."""
    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    with _rate_limit_lock:
        timestamps = _message_timestamps[session_id]

        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if len(timestamps) >= MAX_MESSAGES_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail="Chat rate limit exceeded. Please try again shortly.",
                headers={"Retry-After": "60"},
            )

        timestamps.append(now)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_guest_session(db: Session) -> tuple[ChatSession, str]:
    token = secrets.token_urlsafe(32)

    session = ChatSession(
        guest_token_hash=_hash_token(token),
        user_id=None,
        expires_at=_utcnow() + timedelta(
            hours=SESSION_LIFETIME_HOURS
        ),
    )

    db.add(session)

    try:
        db.commit()
        db.refresh(session)
    except Exception:
        db.rollback()
        raise

    return session, token


def _get_guest_session(
    db: Session,
    session_id: int,
    token: str,
) -> ChatSession:
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.guest_token_hash == _hash_token(token),
        )
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found",
        )

    if session.expires_at and session.expires_at <= _utcnow():
        raise HTTPException(
            status_code=401,
            detail="Chat session expired",
        )

    return session


def _parse_price(query: str) -> Decimal | None:
    match = re.search(
        r"(?:under|below|less than|at most|maximum|max|"
        r"budget(?: of)?|within|up to)\s*"
        r"(?:₹|rs\.?\s*|inr\s*)?([0-9]+(?:\.[0-9]{1,2})?)",
        query,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return Decimal(match.group(1))


def _search_listings(db: Session, query: str):
    price_limit = _parse_price(query)

    normalized = query.lower()
    normalized = re.sub(
        r"(?:under|below|less than|at most|maximum|max|"
        r"budget(?: of)?|within|up to)\s*"
        r"(?:₹|rs\.?\s*|inr\s*)?[0-9]+(?:\.[0-9]{1,2})?",
        " ",
        normalized,
        flags=re.IGNORECASE,
    )

    normalized = re.sub(r"[^\w\s]", " ", normalized)

    terms = [
        term
        for term in normalized.split()
        if term not in STOP_WORDS and not term.isdigit()
    ]

    statement = (
        select(Listing, Category.name)
        .join(Category, Category.id == Listing.category_id)
        .where(
            Listing.status == "available",
            Category.is_active.is_(True),
        )
    )

    if price_limit is not None:
        statement = statement.where(Listing.price <= price_limit)

    # Each remaining keyword must match the title, description,
    # or category. Values are parameterized by SQLAlchemy.
    from sqlalchemy import or_

    for term in terms:
        pattern = f"%{term}%"
        statement = statement.where(
            or_(
                Listing.title.ilike(pattern),
                Listing.description.ilike(pattern),
                Category.name.ilike(pattern),
            )
        )

    statement = statement.order_by(
        Listing.created_at.desc(),
        Listing.id.desc(),
    ).limit(MAX_RESULTS)

    rows = db.execute(statement).all()

    results = []
    for listing, category_name in rows:
        image = db.scalar(
            select(ListingImage.image_url)
            .where(ListingImage.listing_id == listing.id)
            .order_by(ListingImage.position.asc())
            .limit(1)
        )

        results.append({
            "listing_id": listing.id,
            "title": listing.title,
            "price": listing.price,
            "currency": listing.currency,
            "category": category_name,
            "condition": listing.condition,
            "image_url": image,
        })

    return results


def process_chat_message(
    db: Session,
    session_id: int,
    token: str,
    message: str,
) -> dict:
    if not message or not message.strip():
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty",
        )

    if len(message) > 1000:
        raise HTTPException(
            status_code=422,
            detail="Message cannot exceed 1000 characters",
        )

    chat_session = _get_guest_session(db, session_id, token)
    _check_message_rate_limit(chat_session.id)
    started = time.perf_counter()

    try:
        user_message = ChatMessage(
            session_id=chat_session.id,
            role="user",
            content=message.strip(),
        )
        db.add(user_message)
        db.flush()

        listings = _search_listings(db, message)
        count = len(listings)

        if count:
            response_text = (
                f"I found {count} matching available listing(s). "
                "Here are the results from the marketplace."
            )
        else:
            response_text = (
                "I couldn't find any available listings matching "
                "that search. Try different keywords or a higher "
                "price limit."
            )

        assistant_message = ChatMessage(
            session_id=chat_session.id,
            role="assistant",
            content=response_text,
        )
        db.add(assistant_message)

        chat_session.last_activity_at = _utcnow()

        elapsed_ms = int((time.perf_counter() - started) * 1000)

        db.add(
            AIQuery(
                user_id=None,
                query_text=message.strip(),
                result_count=count,
                latency_ms=elapsed_ms,
            )
        )

        db.commit()

        return {
            "session_id": chat_session.id,
            "message": response_text,
            "result_count": count,
            "listings": listings,
        }

    except Exception:
        db.rollback()
        raise

def create_chat_feedback(
    db: Session,
    session_id: int,
    token: str,
    rating: str,
    message_id: int | None = None,
    comments: str | None = None,
) -> dict:
    # Validate the guest token and ensure the session is still active.
    chat_session = _get_guest_session(db, session_id, token)

    if rating not in {"helpful", "not_helpful"}:
        raise HTTPException(
            status_code=422,
            detail="Rating must be helpful or not_helpful",
        )

    if comments is not None:
        comments = comments.strip()
        if not comments:
            comments = None

    if message_id is not None:
        message = db.scalar(
            select(ChatMessage).where(
                ChatMessage.id == message_id,
                ChatMessage.session_id == chat_session.id,
                ChatMessage.role == "assistant",
            )
        )

        if message is None:
            raise HTTPException(
                status_code=404,
                detail="Assistant message not found in this session",
            )

    feedback = ChatFeedback(
        session_id=chat_session.id,
        message_id=message_id,
        rating=rating,
        comments=comments,
    )

    try:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
    except Exception:
        db.rollback()
        raise

    return {
        "feedback_id": feedback.id,
        "session_id": feedback.session_id,
        "message_id": feedback.message_id,
        "rating": feedback.rating,
        "comments": feedback.comments,
    }