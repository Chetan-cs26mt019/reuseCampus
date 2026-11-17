import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import (
    Category,
    Listing,
    ModerationAction,
    User,
)
from app.services.moderation import (
    close_report,
    create_report,
    list_reports,
    review_report,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def moderation_setup(db):
    seller = User(
        email="seller@example.test",
        username="seller",
        password_hash="test-hash",
        full_name="Seller",
    )
    reporter = User(
        email="reporter@example.test",
        username="reporter",
        password_hash="test-hash",
        full_name="Reporter",
    )
    moderator = User(
        email="moderator@example.test",
        username="moderator",
        password_hash="test-hash",
        full_name="Moderator",
        role="moderator",
    )
    outsider = User(
        email="outsider@example.test",
        username="outsider",
        password_hash="test-hash",
        full_name="Outsider",
    )
    category = Category(name="Books")

    db.add_all([
        seller,
        reporter,
        moderator,
        outsider,
        category,
    ])
    db.flush()

    listing = Listing(
        seller_id=seller.id,
        category_id=category.id,
        title="Used textbook",
        description="A book for testing",
        price=200,
        condition="good",
        status="available",
    )
    db.add(listing)
    db.commit()

    return seller, reporter, moderator, outsider, listing


def test_create_report(db, moderation_setup):
    _, reporter, _, _, listing = moderation_setup

    report = create_report(
        db,
        reporter,
        listing.id,
        "misleading_listing",
        "The description appears inaccurate",
    )

    assert report.listing_id == listing.id
    assert report.reporter_id == reporter.id
    assert report.status == "open"


def test_seller_cannot_report_own_listing(
    db, moderation_setup
):
    seller, _, _, _, listing = moderation_setup

    with pytest.raises(HTTPException) as error:
        create_report(
            db,
            seller,
            listing.id,
            "other",
            "Test report",
        )

    assert error.value.status_code == 400


def test_non_moderator_cannot_list_reports(
    db, moderation_setup
):
    _, reporter, _, _, listing = moderation_setup

    create_report(
        db, reporter, listing.id, "spam", "Test report"
    )

    with pytest.raises(HTTPException) as error:
        list_reports(db, reporter)

    assert error.value.status_code == 403


def test_moderator_can_dismiss_and_audit_report(
    db, moderation_setup
):
    _, reporter, moderator, _, listing = moderation_setup

    report = create_report(
        db, reporter, listing.id, "spam", "Unwanted content"
    )

    result = review_report(
        db,
        moderator,
        report.id,
        "dismiss",
        "Reviewed; no violation found",
    )

    assert result.status == "dismissed"
    assert result.reviewer_id == moderator.id
    assert result.reviewed_at is not None

    audit = db.query(ModerationAction).filter_by(
        report_id=report.id
    ).one()

    assert audit.moderator_id == moderator.id
    assert audit.action == "dismiss"


def test_moderator_can_hide_listing(
    db, moderation_setup
):
    _, reporter, moderator, _, listing = moderation_setup

    report = create_report(
        db,
        reporter,
        listing.id,
        "misleading_listing",
        "Needs review",
    )

    result = review_report(
        db,
        moderator,
        report.id,
        "hide_listing",
        "Hidden pending policy review",
    )

    db.refresh(listing)

    assert result.status == "action_taken"
    assert listing.status == "hidden"
    assert listing.hidden_at is not None

    audit = db.query(ModerationAction).filter_by(
        report_id=report.id
    ).one()

    assert audit.action == "hide_listing"


def test_report_decision_can_be_revised_before_closing(
    db, moderation_setup
):
    _, reporter, moderator, _, listing = moderation_setup

    report = create_report(
        db, reporter, listing.id, "spam", "Test report"
    )
    review_report(db, moderator, report.id, "dismiss", "Initial review")
    result = review_report(
        db, moderator, report.id, "hide_listing", "New evidence found"
    )

    db.refresh(listing)
    assert result.status == "action_taken"
    assert listing.status == "hidden"
    actions = db.query(ModerationAction).filter_by(report_id=report.id).order_by(ModerationAction.id).all()
    assert [item.action for item in actions] == ["dismiss", "hide_listing"]



def test_report_list_includes_reported_product_details_and_image(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    from app.models import ListingImage
    db.add(ListingImage(listing_id=listing.id, image_url="/uploads/test-book.jpg", alt_text="Book cover", position=0))
    db.commit()
    report = create_report(db, reporter, listing.id, "spam", "Please review")
    result = list_reports(db, moderator)
    assert result[0]["id"] == report.id
    assert result[0]["listing_title"] == "Used textbook"
    assert result[0]["listing_image"] == "/uploads/test-book.jpg"


def test_moderator_can_close_reviewed_report_and_audit_it(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    report = create_report(db, reporter, listing.id, "spam", "Please review")
    review_report(db, moderator, report.id, "hide_listing", "Policy violation")
    result = close_report(db, moderator, report.id, "Action completed")
    assert result.status == "closed"
    assert result.closed_by == moderator.id
    assert result.closed_at is not None
    audit = db.query(ModerationAction).filter_by(report_id=report.id, action="close_report").one()
    assert audit.moderator_id == moderator.id


def test_open_report_cannot_be_closed_before_review(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    report = create_report(db, reporter, listing.id, "spam", "Please review")
    with pytest.raises(HTTPException) as error:
        close_report(db, moderator, report.id, "Premature close")
    assert error.value.status_code == 409


def test_closed_report_cannot_be_reviewed_or_closed_again(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    report = create_report(db, reporter, listing.id, "spam", "Please review")
    review_report(db, moderator, report.id, "dismiss", "No violation")
    close_report(db, moderator, report.id, "Review completed")
    with pytest.raises(HTTPException) as review_error:
        review_report(db, moderator, report.id, "hide_listing", "Try again")
    assert review_error.value.status_code == 409
    with pytest.raises(HTTPException) as close_error:
        close_report(db, moderator, report.id, "Try closing again")
    assert close_error.value.status_code == 409



def test_moderator_can_unhide_listing_before_closing_report(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    report = create_report(db, reporter, listing.id, "spam", "Review listing")
    review_report(db, moderator, report.id, "hide_listing", "Temporarily hide")

    result = review_report(db, moderator, report.id, "unhide_listing", "Investigation cleared")
    db.refresh(listing)

    assert result.status == "action_taken"
    assert listing.status == "available"
    assert listing.hidden_at is None
    actions = db.query(ModerationAction).filter_by(report_id=report.id).order_by(ModerationAction.id).all()
    assert [item.action for item in actions] == ["hide_listing", "unhide_listing"]


def test_dismissing_report_reverses_its_own_hide(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    report = create_report(db, reporter, listing.id, "spam", "Review listing")
    review_report(db, moderator, report.id, "hide_listing", "Temporarily hide")
    review_report(db, moderator, report.id, "dismiss", "No violation found")
    db.refresh(listing)

    assert report.status == "dismissed"
    assert listing.status == "available"
    assert listing.hidden_at is None
    actions = db.query(ModerationAction).filter_by(report_id=report.id).order_by(ModerationAction.id).all()
    assert [item.action for item in actions] == ["hide_listing", "unhide_listing", "dismiss"]


def test_moderator_can_change_dismissed_decision_to_hide(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    report = create_report(db, reporter, listing.id, "spam", "Review listing")
    review_report(db, moderator, report.id, "dismiss", "Initial review")
    review_report(db, moderator, report.id, "hide_listing", "New evidence found")
    db.refresh(listing)

    assert report.status == "action_taken"
    assert listing.status == "hidden"
    assert listing.hidden_at is not None


def test_removed_listing_cannot_be_unhidden_or_decision_changed(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    report = create_report(db, reporter, listing.id, "prohibited_item", "Review listing")
    review_report(db, moderator, report.id, "remove_listing", "Confirmed prohibited item")

    with pytest.raises(HTTPException) as error:
        review_report(db, moderator, report.id, "unhide_listing", "Try restore")
    assert error.value.status_code == 409
    db.refresh(listing)
    assert listing.status == "removed"
    assert listing.removed_at is not None


def test_closed_report_remains_immutable_after_revisions(db, moderation_setup):
    _, reporter, moderator, _, listing = moderation_setup
    report = create_report(db, reporter, listing.id, "spam", "Review listing")
    review_report(db, moderator, report.id, "hide_listing", "Hide temporarily")
    review_report(db, moderator, report.id, "unhide_listing", "Restore after review")
    close_report(db, moderator, report.id, "Review complete")

    with pytest.raises(HTTPException) as error:
        review_report(db, moderator, report.id, "hide_listing", "Try after close")
    assert error.value.status_code == 409
