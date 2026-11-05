from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.recommendations import RecommendationResponse
from app.schemas.pagination import PaginatedResponse
from app.services.pagination import paginate_items
from app.services.recommendations import (
    personalized_recommendations,
    popular_recommendations,
    similar_recommendations,
)

router = APIRouter(prefix="/recommendations", tags=["AI Recommendations"])


def format_results(results):
    fields = (
        "id", "seller_id", "category_id", "title", "description",
        "price", "currency", "condition", "status",
        "created_at", "updated_at",
    )

    return [
        {
            **{field: getattr(item["listing"], field) for field in fields},
            "similarity_score": item["score"],
            "recommendation_reason": item["reason"],
        }
        for item in results
    ]


@router.get("/popular", response_model=PaginatedResponse[RecommendationResponse])
def get_popular(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    results = popular_recommendations(db, limit=None)
    return paginate_items(format_results(results), page, size)


@router.get("/similar/{listing_id}", response_model=PaginatedResponse[RecommendationResponse])
def get_similar(
    listing_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    results = similar_recommendations(db, listing_id, limit=None)
    return paginate_items(format_results(results), page, size)


@router.get("", response_model=PaginatedResponse[RecommendationResponse])
def get_personalized(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = personalized_recommendations(db, current_user.id, limit=None)
    return paginate_items(format_results(results), page, size)
