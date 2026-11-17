from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Listing,
    ListingImage,
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
) -> list[dict]:
    _require_moderator(moderator)

    first_image = (
        select(ListingImage.image_url)
        .where(ListingImage.listing_id == Listing.id)
        .order_by(ListingImage.position.asc(), ListingImage.id.asc())
        .limit(1)
        .scalar_subquery()
    )
    statement = (
        select(Report, Listing, first_image.label("listing_image"))
        .join(Listing, Listing.id == Report.listing_id)
        .order_by(Report.created_at.desc(), Report.id.desc())
    )
    rows = db.execute(statement).all()
    report_ids = [report.id for report, _, _ in rows]
    action_rows = []
    if report_ids:
        action_rows = db.scalars(
            select(ModerationAction)
            .where(ModerationAction.report_id.in_(report_ids))
            .order_by(ModerationAction.created_at.asc(), ModerationAction.id.asc())
        ).all()

    actions_by_report: dict[int, list[dict]] = {}
    for action in action_rows:
        actions_by_report.setdefault(action.report_id, []).append({
            "id": action.id,
            "report_id": action.report_id,
            "listing_id": action.listing_id,
            "moderator_id": action.moderator_id,
            "action": action.action,
            "reason": action.reason,
            "created_at": action.created_at,
        })

    results = []
    for report, listing, image_url in rows:
        results.append({
            "id": report.id,
            "listing_id": report.listing_id,
            "reporter_id": report.reporter_id,
            "reviewer_id": report.reviewed_by,
            "reason": report.reason,
            "details": report.details,
            "status": report.status,
            "created_at": report.created_at,
            "reviewed_at": report.reviewed_at,
            "closed_by": report.closed_by,
            "closed_at": report.closed_at,
            "listing_title": listing.title,
            "listing_price": float(listing.price),
            "listing_condition": listing.condition,
            "listing_status": listing.status,
            "listing_hidden": listing.hidden_at is not None,
            "listing_removed": listing.removed_at is not None,
            "listing_image": image_url,
            "actions": actions_by_report.get(report.id, []),
        })
    return results


def review_report(
    db: Session,
    moderator: User,
    report_id: int,
    action: str,
    reason: str,
) -> Report:
    """Apply or revise an unclosed report decision, preserving every step."""
    _require_moderator(moderator)

    try:
        report = db.scalar(
            select(Report).where(Report.id == report_id).with_for_update()
        )
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        if report.status == "closed" or report.closed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Closed reports cannot be changed",
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

        now = datetime.now(UTC).replace(tzinfo=None)
        latest_action = db.scalar(
            select(ModerationAction)
            .where(ModerationAction.report_id == report.id)
            .order_by(ModerationAction.id.desc())
            .limit(1)
        )

        if listing.removed_at is not None or listing.status == "removed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This listing was permanently removed and cannot be changed",
            )

        if action == "hide_listing":
            if listing.status == "sold":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A sold listing cannot be hidden",
                )
            if listing.hidden_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This listing is already hidden",
                )
            listing.status = "hidden"
            listing.hidden_at = now
            report.status = "action_taken"

        elif action == "unhide_listing":
            if latest_action is None or latest_action.action != "hide_listing":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This report does not have an active hide decision to reverse",
                )
            if listing.hidden_at is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="The listing is not currently hidden",
                )
            listing.status = "available"
            listing.hidden_at = None
            report.status = "action_taken"

        elif action == "remove_listing":
            listing.status = "removed"
            listing.removed_at = now
            report.status = "action_taken"

        elif action == "dismiss":
            # If this report's latest decision hid the listing, undo that hide.
            # Do not unhide a listing hidden by another moderation report.
            if latest_action is not None and latest_action.action == "hide_listing":
                if listing.hidden_at is not None:
                    listing.status = "available"
                    listing.hidden_at = None
                    db.add(ModerationAction(
                        report_id=report.id,
                        listing_id=listing.id,
                        moderator_id=moderator.id,
                        action="unhide_listing",
                        reason="Automatically restored because this report was dismissed.",
                    ))
            report.status = "dismissed"

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported moderation action",
            )

        report.reviewed_by = moderator.id
        report.reviewed_at = now
        db.add(ModerationAction(
            report_id=report.id,
            listing_id=listing.id,
            moderator_id=moderator.id,
            action=action,
            reason=reason,
        ))
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise


def close_report(db: Session, moderator: User, report_id: int, reason: str) -> Report:
    """Close a reviewed report; closed reports cannot be modified afterwards."""
    _require_moderator(moderator)
    try:
        report = db.scalar(
            select(Report).where(Report.id == report_id).with_for_update()
        )
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        if report.status not in {"action_taken", "dismissed"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only reviewed reports can be closed",
            )
        now = datetime.now(UTC).replace(tzinfo=None)
        report.status = "closed"
        report.closed_by = moderator.id
        report.closed_at = now
        db.add(ModerationAction(
            report_id=report.id,
            listing_id=report.listing_id,
            moderator_id=moderator.id,
            action="close_report",
            reason=reason,
        ))
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
