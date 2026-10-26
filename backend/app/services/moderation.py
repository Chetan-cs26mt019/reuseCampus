from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Listing,
    ModerationAction,
    Report,
    User,
)


def create_report(
    db: Session,
    reporter: User,
    listing_id: int,
    reason: str,
    details: str | None,
) -> Report:
    listing = db.get(Listing, listing_id)

    if listing is None or listing.status in {"removed"}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    if reporter.id == listing.seller_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot report your own listing",
        )

    report = Report(
        listing_id=listing.id,
        reporter_id=reporter.id,
        reason=reason,
        details=details,
        status="open",
    )

    db.add(report)

    try:
        db.commit()
        db.refresh(report)
    except Exception:
        db.rollback()
        raise

    return report


def list_reports(
    db: Session,
    moderator: User,
) -> list[Report]:
    _require_moderator(moderator)

    statement = (
        select(Report)
        .order_by(Report.created_at.desc(), Report.id.desc())
    )

    return list(db.scalars(statement).all())


def review_report(
    db: Session,
    moderator: User,
    report_id: int,
    action: str,
    reason: str,
) -> Report:
    _require_moderator(moderator)

    try:
        report = db.scalar(
            select(Report)
            .where(Report.id == report_id)
            .with_for_update()
        )

        if report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        if report.status != "open":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only open reports can be reviewed",
            )

        listing = db.scalar(
            select(Listing)
            .where(Listing.id == report.listing_id)
            .with_for_update()
        )

        if listing is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Reported listing no longer exists",
            )

        if action == "dismiss":
            report.status = "dismissed"
            audit_action = "dismiss"

        elif action == "hide_listing":
            if listing.status in {"removed", "sold"}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This listing cannot be hidden in its current state",
                )

            listing.status = "hidden"
            listing.hidden_at = datetime.now(
                timezone.utc
            ).replace(tzinfo=None)
            report.status = "action_taken"
            audit_action = "hide_listing"

        elif action == "remove_listing":
            if listing.status == "removed":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Listing has already been removed",
                )

            listing.status = "removed"
            listing.removed_at = datetime.now(
                timezone.utc
            ).replace(tzinfo=None)
            report.status = "action_taken"
            audit_action = "remove_listing"

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported moderation action",
            )

        report.reviewer_id = moderator.id
        report.reviewed_at = datetime.now(
            timezone.utc
        ).replace(tzinfo=None)

        db.add(
            ModerationAction(
                report_id=report.id,
                listing_id=listing.id,
                moderator_id=moderator.id,
                action=audit_action,
                reason=reason,
            )
        )

        db.commit()
        db.refresh(report)
        return report

    except Exception:
        db.rollback()
        raise


def _require_moderator(user: User) -> None:
    if user.role != "moderator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator privileges required",
        )
