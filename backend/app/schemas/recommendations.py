from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
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
    similarity_score: float | None = None
    recommendation_reason: str
