from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_category_id: int | None
    is_active: bool


class ListingCreate(BaseModel):
    category_id: int = Field(gt=0)
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    condition: str = Field(min_length=1, max_length=30)


class ListingUpdate(BaseModel):
    category_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(
        default=None, min_length=1, max_length=10000
    )
    price: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    condition: str | None = Field(
        default=None, min_length=1, max_length=30
    )


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    seller_id: int
    category_id: int
    title: str
    description: str
    price: Decimal
    currency: str
    condition: str
    status: str
    created_at: datetime
    updated_at: datetime


class ListingImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    image_url: str
    alt_text: str | None
    position: int
