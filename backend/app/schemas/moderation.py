from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    reason: Literal[
        "spam",
        "fraud",
        "prohibited_item",
        "misleading_listing",
        "harassment",
        "other",
    ]
    details: str | None = Field(default=None, max_length=2000)


class ReportReview(BaseModel):
    action: Literal["dismiss", "hide_listing", "unhide_listing", "remove_listing"]
    reason: str = Field(min_length=3, max_length=1000)


class ReportClose(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class ModerationActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    listing_id: int
    moderator_id: int
    action: str
    reason: str | None = None
    created_at: datetime


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    reporter_id: int
    reviewer_id: int | None
    reason: str
    details: str | None
    status: str
    created_at: datetime
    reviewed_at: datetime | None
    closed_by: int | None = None
    closed_at: datetime | None = None
    listing_title: str | None = None
    listing_price: float | None = None
    listing_condition: str | None = None
    listing_status: str | None = None
    listing_image: str | None = None
    listing_hidden: bool = False
    listing_removed: bool = False
    actions: list[ModerationActionResponse] = Field(default_factory=list)
