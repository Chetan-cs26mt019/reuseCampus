from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReservationCreate(BaseModel):
    listing_id: int = Field(gt=0)


class ReservationAction(BaseModel):
    action: Literal["accept", "reject", "cancel", "complete"]


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    status: str
    reserved_at: datetime
    completed_at: datetime | None
