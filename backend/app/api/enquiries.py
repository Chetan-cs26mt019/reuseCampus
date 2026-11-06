from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
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
    return paginate_items(list_my_enquiries(db, current_user), page, size)


@router.get(
    "/{enquiry_id}",
    response_model=EnquiryResponse,
)
def get_enquiry_endpoint(
    enquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_enquiry_for_participant(
        db, current_user, enquiry_id
    )


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
    return paginate_items(
        list_enquiry_messages(db, current_user, enquiry_id), page, size
    )


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