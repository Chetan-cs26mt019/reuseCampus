from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnquiryCreate(BaseModel):
    listing_id: int = Field(gt=0)


class EnquiryMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class EnquiryMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enquiry_id: int
    sender_id: int
    body: str
    created_at: datetime
    read_at: datetime | None


class EnquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    status: str
    created_at: datetime
    updated_at: datetime