from decimal import Decimal

from pydantic import BaseModel, Field
from typing import Literal


class ChatSessionResponse(BaseModel):
    session_id: int
    guest_token: str


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatListingResult(BaseModel):
    listing_id: int
    title: str
    price: Decimal
    currency: str
    category: str
    condition: str
    image_url: str | None = None


class ChatMessageResponse(BaseModel):
    session_id: int
    message: str
    result_count: int
    listings: list[ChatListingResult]


class ChatFeedbackRequest(BaseModel):
    rating: Literal["helpful", "not_helpful"]
    message_id: int | None = Field(default=None, gt=0)
    comments: str | None = Field(default=None, max_length=1000)


class ChatFeedbackResponse(BaseModel):
    feedback_id: int
    session_id: int
    message_id: int | None
    rating: str
    comments: str | None