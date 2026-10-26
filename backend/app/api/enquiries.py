from fastapi import APIRouter, Depends, status
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
from app.services.enquiries import (
    create_enquiry,
    get_enquiry_for_participant,
    list_enquiry_messages,
    list_my_enquiries,
    send_enquiry_message,
)


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


@router.get("", response_model=list[EnquiryResponse])
def list_enquiries_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_my_enquiries(db, current_user)


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
    response_model=list[EnquiryMessageResponse],
)
def list_messages_endpoint(
    enquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_enquiry_messages(
        db, current_user, enquiry_id
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