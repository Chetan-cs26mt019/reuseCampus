from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Enquiry, EnquiryMessage, Listing, User


def get_or_create_enquiry(
    db: Session,
    buyer: User,
    listing_id: int,
) -> tuple[Enquiry, bool]:
    """Return the buyer's existing thread for a listing, or create one.

    The boolean is True only when a new enquiry was inserted.
    Existing threads are returned even if the listing is no longer available,
    so the buyer can continue to access the conversation already started.
    """
    listing = db.scalar(
        select(Listing).where(Listing.id == listing_id)
    )

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    if listing.seller_id == buyer.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot enquire about your own listing",
        )

    existing = db.scalar(
        select(Enquiry)
        .where(
            Enquiry.listing_id == listing.id,
            Enquiry.buyer_id == buyer.id,
        )
        .order_by(Enquiry.created_at.asc(), Enquiry.id.asc())
    )
    if existing is not None:
        return existing, False

    if listing.status != "available":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Available listing not found",
        )

    enquiry = Enquiry(
        listing_id=listing.id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        status="open",
    )
    db.add(enquiry)

    try:
        db.commit()
        db.refresh(enquiry)
    except Exception:
        db.rollback()
        # A second request may have created the same thread concurrently.
        # Re-read it before surfacing the database error.
        existing = db.scalar(
            select(Enquiry)
            .where(
                Enquiry.listing_id == listing.id,
                Enquiry.buyer_id == buyer.id,
            )
            .order_by(Enquiry.created_at.asc(), Enquiry.id.asc())
        )
        if existing is not None:
            return existing, False
        raise

    return enquiry, True


def create_enquiry(
    db: Session,
    buyer: User,
    listing_id: int,
) -> Enquiry:
    """Compatibility wrapper used by service callers and tests."""
    enquiry, _created = get_or_create_enquiry(db, buyer, listing_id)
    return enquiry


def list_my_enquiries(
    db: Session,
    user: User,
) -> list[Enquiry]:
    statement = (
        select(Enquiry)
        .where(
            (Enquiry.buyer_id == user.id)
            | (Enquiry.seller_id == user.id)
        )
        .order_by(Enquiry.created_at.desc())
    )

    return list(db.scalars(statement).all())


def get_enquiry_for_participant(
    db: Session,
    user: User,
    enquiry_id: int,
) -> Enquiry:
    enquiry = db.scalar(
        select(Enquiry).where(Enquiry.id == enquiry_id)
    )

    if enquiry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found",
        )

    if user.id not in {enquiry.buyer_id, enquiry.seller_id}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found",
        )

    return enquiry


def list_enquiry_messages(
    db: Session,
    user: User,
    enquiry_id: int,
) -> list[EnquiryMessage]:
    get_enquiry_for_participant(db, user, enquiry_id)

    statement = (
        select(EnquiryMessage)
        .where(EnquiryMessage.enquiry_id == enquiry_id)
        .order_by(
            EnquiryMessage.created_at.asc(),
            EnquiryMessage.id.asc(),
        )
    )

    return list(db.scalars(statement).all())


def send_enquiry_message(
    db: Session,
    user: User,
    enquiry_id: int,
    body: str,
) -> EnquiryMessage:
    enquiry = get_enquiry_for_participant(
        db, user, enquiry_id
    )

    if enquiry.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This enquiry is closed",
        )

    message = EnquiryMessage(
        enquiry_id=enquiry.id,
        sender_id=user.id,
        body=body,
    )

    db.add(message)

    try:
        db.commit()
        db.refresh(message)
    except Exception:
        db.rollback()
        raise

    return message