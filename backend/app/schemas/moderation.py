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
    action: Literal["dismiss", "hide_listing", "remove_listing"]
    reason: str = Field(min_length=3, max_length=1000)


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


class ModerationActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    listing_id: int
    moderator_id: int
    action: str
    reason: str
    created_at: datetime
