from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ListingView, SearchHistory


def _now():
    return datetime.now(UTC).replace(tzinfo=None)


def record_search(db: Session, user_id: int, query: str) -> None:
    normalized = " ".join(query.strip().lower().split())[:200]
    if not normalized:
        return

    entry = db.scalar(
        select(SearchHistory).where(
            SearchHistory.user_id == user_id,
            SearchHistory.normalized_query == normalized,
        )
    )
    now = _now()
    if entry is None:
        entry = SearchHistory(
            user_id=user_id,
            normalized_query=normalized,
            search_count=1,
            last_searched_at=now,
        )
        db.add(entry)
    else:
        entry.search_count += 1
        entry.last_searched_at = now

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def record_listing_view(db: Session, user_id: int, listing_id: int) -> None:
    entry = db.get(ListingView, (user_id, listing_id))
    now = _now()
    if entry is None:
        entry = ListingView(
            user_id=user_id,
            listing_id=listing_id,
            view_count=1,
            first_viewed_at=now,
            last_viewed_at=now,
        )
        db.add(entry)
    else:
        entry.view_count += 1
        entry.last_viewed_at = now

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
