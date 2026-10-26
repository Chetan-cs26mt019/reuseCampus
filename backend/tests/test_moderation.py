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
    Report,
    User,
)
from app.services.moderation import (
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


def test_report_cannot_be_reviewed_twice(
    db, moderation_setup
):
    _, reporter, moderator, _, listing = moderation_setup

    report = create_report(
        db, reporter, listing.id, "spam", "Test report"
    )

    review_report(
        db, moderator, report.id, "dismiss", "Reviewed"
    )

    with pytest.raises(HTTPException) as error:
        review_report(
            db,
            moderator,
            report.id,
            "dismiss",
            "Attempted second review",
        )

    assert error.value.status_code == 409
