from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Reservation, User
from app.schemas.reservation import (
    ReservationAction,
    ReservationCreate,
    ReservationResponse,
)
from app.services.reservations import (
    change_reservation_status,
    create_reservation,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def request_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_reservation(
        db=db,
        buyer=current_user,
        listing_id=payload.listing_id,
    )


@router.get("", response_model=list[ReservationResponse])
def list_my_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Reservation)
        .where(
            or_(
                Reservation.buyer_id == current_user.id,
                Reservation.seller_id == current_user.id,
            )
        )
        .order_by(Reservation.created_at.desc())
    )

    return list(db.scalars(statement).all())


@router.get("/{order_id}", response_model=ReservationResponse)
def get_reservation(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation = db.scalar(
        select(Reservation).where(
            Reservation.id == order_id,
            or_(
                Reservation.buyer_id == current_user.id,
                Reservation.seller_id == current_user.id,
            ),
        )
    )

    if reservation is None:
        # Avoid revealing whether another user's reservation exists.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    return reservation


@router.patch("/{order_id}", response_model=ReservationResponse)
def update_reservation(
    order_id: int,
    payload: ReservationAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return change_reservation_status(
        db=db,
        actor=current_user,
        reservation_id=order_id,
        action=payload.action,
    )
