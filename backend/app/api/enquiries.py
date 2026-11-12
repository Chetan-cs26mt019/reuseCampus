from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Enquiry, EnquiryMessage, Listing, ListingImage, User
from app.schemas.enquiry import (
    EnquiryCreate,
    EnquiryMessageCreate,
    EnquiryMessageResponse,
    EnquiryResponse,
)
from app.schemas.pagination import PaginatedResponse
from app.services.enquiries import (
    create_enquiry,
    get_enquiry_for_participant,
    list_enquiry_messages,
    list_my_enquiries,
    send_enquiry_message,
)
from app.services.pagination import paginate_items

router = APIRouter(
    prefix="/enquiry-threads",
    tags=["Enquiries"],
)


@router.post(
    "",
    response_model=EnquiryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enquiry_endpoint(
    payload: EnquiryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_enquiry(
        db, current_user, payload.listing_id
    )


@router.get("", response_model=PaginatedResponse[EnquiryResponse])
def list_enquiries_endpoint(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enquiries = list_my_enquiries(db, current_user)
    items = [_enquiry_view(db, item) for item in enquiries]
    return paginate_items(items, page, size)


@router.get(
    "/{enquiry_id}",
    response_model=EnquiryResponse,
)
def get_enquiry_endpoint(
    enquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enquiry = get_enquiry_for_participant(db, current_user, enquiry_id)
    return _enquiry_view(db, enquiry)


@router.get(
    "/{enquiry_id}/messages",
    response_model=PaginatedResponse[EnquiryMessageResponse],
)
def list_messages_endpoint(
    enquiry_id: int,
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    messages = list_enquiry_messages(db, current_user, enquiry_id)
    items = []
    for message in messages:
        sender = db.get(User, message.sender_id)
        items.append({**message.__dict__, "sender_name": sender.full_name if sender else "User"})
    return paginate_items(items, page, size)


@router.post(
    "/{enquiry_id}/messages",
    response_model=EnquiryMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message_endpoint(
    enquiry_id: int,
    payload: EnquiryMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return send_enquiry_message(
        db,
        current_user,
        enquiry_id,
        payload.body,
    )

def _enquiry_view(db: Session, enquiry: Enquiry) -> dict:
    listing = db.get(Listing, enquiry.listing_id)
    buyer = db.get(User, enquiry.buyer_id)
    seller = db.get(User, enquiry.seller_id)
    image = db.scalar(select(ListingImage.image_url).where(
        ListingImage.listing_id == enquiry.listing_id
    ).order_by(ListingImage.position).limit(1))
    return {
        **enquiry.__dict__,
        "listing_title": listing.title if listing else "Unavailable product",
        "listing_price": float(listing.price) if listing else None,
        "listing_image": image,
        "buyer_name": buyer.full_name if buyer else "Buyer",
        "seller_name": seller.full_name if seller else "Seller",
    }
