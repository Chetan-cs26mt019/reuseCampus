from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Listing, Reservation, User


ACTIVE_RESERVATION_STATUSES = {"requested", "accepted"}


def create_reservation(
    db: Session,
    buyer: User,
    listing_id: int,
) -> Reservation:
    """
    Reserve an available listing.

    Locking the listing row serializes competing reservation
    requests for the same listing in MySQL/InnoDB.
    """
    listing = db.scalar(
        select(Listing)
        .where(Listing.id == listing_id)
        .with_for_update()
    )

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    if listing.seller_id == buyer.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot reserve your own listing",
        )

    if listing.status != "available":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing is not available",
        )

    existing = db.scalar(
        select(Reservation.id)
        .where(
            Reservation.listing_id == listing.id,
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        )
        .limit(1)
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This listing already has an active reservation",
        )

    reservation = Reservation(
        listing_id=listing.id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        status="requested",
    )

    listing.status = "reserved"
    db.add(reservation)

    try:
        db.commit()
        db.refresh(reservation)
    except Exception:
        db.rollback()
        raise

    return reservation


def change_reservation_status(
    db: Session,
    actor: User,
    reservation_id: int,
    action: str,
) -> Reservation:
    """Enforce reservation lifecycle and participant permissions."""

    # First find the listing ID without acquiring a row lock.
    listing_id = db.scalar(
        select(Reservation.listing_id).where(
            Reservation.id == reservation_id
        )
    )

    if listing_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    try:
        # Always lock the listing before locking its reservation.
        listing = db.scalar(
            select(Listing)
            .where(Listing.id == listing_id)
            .with_for_update()
        )

        if listing is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The associated listing no longer exists",
            )

        reservation = db.scalar(
            select(Reservation)
            .where(Reservation.id == reservation_id)
            .with_for_update()
        )

        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found",
            )

        # Recheck that the reservation still belongs to this listing.
        if reservation.listing_id != listing.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Reservation changed; please retry",
            )

        is_buyer = actor.id == reservation.buyer_id
        is_seller = actor.id == reservation.seller_id

        if not is_buyer and not is_seller:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this reservation",
            )

        if action in {"accept", "reject"}:
            if not is_seller:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the seller can accept or reject",
                )

            if reservation.status != "requested":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only requested reservations can be accepted or rejected",
                )

            if action == "accept":
                reservation.status = "accepted"
            else:
                reservation.status = "rejected"
                db.flush()
                _release_listing_if_no_active_reservations(db, listing)

        elif action == "cancel":
            if not is_buyer:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the buyer can cancel this reservation",
                )

            if reservation.status != "requested":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only requested reservations can be cancelled",
                )

            reservation.status = "cancelled"
            db.flush()
            _release_listing_if_no_active_reservations(db, listing)

        elif action == "complete":
            if reservation.status != "accepted":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only accepted reservations can be completed",
                )

            if listing.status != "reserved":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Listing is not in the reserved state",
                )

            from datetime import datetime, timezone

            reservation.status = "completed"
            listing.status = "sold"
            reservation.completed_at = datetime.now(
                timezone.utc
            ).replace(tzinfo=None)

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported reservation action",
            )

        db.commit()
        db.refresh(reservation)
        return reservation

    except Exception:
        db.rollback()
        raise

def _release_listing_if_no_active_reservations(
    db: Session,
    listing: Listing,
) -> None:
    """
    Make the listing available again when no active reservation
    remains. Do not override a moderation or sold status.
    """
    if listing.status != "reserved":
        return

    active_id = db.scalar(
        select(Reservation.id)
        .where(
            Reservation.listing_id == listing.id,
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        )
        .limit(1)
    )

    if active_id is None:
        listing.status = "available"
