from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.moderation import (
    ReportCreate,
    ReportResponse,
    ReportReview,
)
from app.services.moderation import (
    create_report,
    list_reports,
    review_report,
)


reports_router = APIRouter(
    prefix="/listings",
    tags=["Reports"],
)

moderation_router = APIRouter(
    prefix="/moderation",
    tags=["Moderation"],
)


@reports_router.post(
    "/{listing_id}/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_report_endpoint(
    listing_id: int,
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_report(
        db,
        current_user,
        listing_id,
        payload.reason,
        payload.details,
    )


@moderation_router.get(
    "/reports",
    response_model=list[ReportResponse],
)
def list_reports_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_reports(db, current_user)


@moderation_router.patch(
    "/reports/{report_id}",
    response_model=ReportResponse,
)
def review_report_endpoint(
    report_id: int,
    payload: ReportReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return review_report(
        db,
        current_user,
        report_id,
        payload.action,
        payload.reason,
    )
