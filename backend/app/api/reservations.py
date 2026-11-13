from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Listing, ListingImage, Reservation, User
from app.schemas.pagination import PaginatedResponse
from app.schemas.reservation import (
    ReservationAction,
    ReservationCreate,
    ReservationResponse,
)
from app.services.pagination import paginate_items
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


@router.get("", response_model=PaginatedResponse[ReservationResponse])
def list_my_reservations(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
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

    reservations = list(db.scalars(statement).all())
    items = [_reservation_view(db, item) for item in reservations]
    return paginate_items(items, page, size)


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

    return _reservation_view(db, reservation)


@router.patch("/{order_id}", response_model=ReservationResponse)
def update_reservation(
    order_id: int,
    payload: ReservationAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation = change_reservation_status(
        db=db, actor=current_user, reservation_id=order_id, action=payload.action
    )
    return _reservation_view(db, reservation)


def _reservation_view(db: Session, reservation: Reservation) -> dict:
    listing = db.get(Listing, reservation.listing_id)
    buyer = db.get(User, reservation.buyer_id)
    seller = db.get(User, reservation.seller_id)
    image = db.scalar(select(ListingImage.image_url).where(
        ListingImage.listing_id == reservation.listing_id
    ).order_by(ListingImage.position).limit(1))
    return {
        **reservation.__dict__,
        "listing_title": listing.title if listing else "Unavailable product",
        "listing_price": float(listing.price) if listing else None,
        "listing_image": image,
        "buyer_name": buyer.full_name if buyer else "Buyer",
        "seller_name": seller.full_name if seller else "Seller",
    }
