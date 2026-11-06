
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AIEmbedding,
    Category,
    Favourite,
    Listing,
    Reservation,
)
from app.services.embedding_model import (
    MODEL_NAME,
    cosine_similarity,
    deserialize_embedding,
    embedding_hash,
    make_embedding,
    serialize_embedding,
)


def listing_text(db: Session, listing: Listing) -> str:
    category = db.get(Category, listing.category_id)
    category_name = category.name if category else ""

    return (
        f"Title: {listing.title}. "
        f"Description: {listing.description}. "
        f"Category: {category_name}. "
        f"Condition: {listing.condition}."
    )


def get_listing_embedding(db: Session, listing: Listing) -> list[float]:
    content = listing_text(db, listing)
    source_hash = embedding_hash(content)

    cached = db.scalar(
        select(AIEmbedding).where(
            AIEmbedding.listing_id == listing.id,
            AIEmbedding.model_version == MODEL_NAME,
            AIEmbedding.source_hash == source_hash,
            AIEmbedding.is_current.is_(True),
        )
    )

    if cached is not None:
        return deserialize_embedding(cached.vector_ref).tolist()

    vector = make_embedding(content)

    # Invalidate older versions for this listing.
    old_embeddings = db.scalars(
        select(AIEmbedding).where(
            AIEmbedding.listing_id == listing.id,
            AIEmbedding.is_current.is_(True),
        )
    ).all()

    for old in old_embeddings:
        old.is_current = False

    db.add(
        AIEmbedding(
            listing_id=listing.id,
            model_version=MODEL_NAME,
            vector_ref=serialize_embedding(vector),
            source_hash=source_hash,
            is_current=True,
        )
    )
    db.commit()

    return vector


def available_listings(db: Session, exclude_seller_id: int | None = None):
    statement = (
        select(Listing)
        .join(Category, Category.id == Listing.category_id)
        .where(
            Listing.status == "available",
            Listing.hidden_at.is_(None),
            Listing.removed_at.is_(None),
            Category.is_active.is_(True),
        )
    )

    if exclude_seller_id is not None:
        statement = statement.where(Listing.seller_id != exclude_seller_id)

    return list(db.scalars(statement.order_by(Listing.created_at.desc())).all())


def popular_recommendations(
    db: Session,
    limit: int | None = 10,
    exclude_seller_id: int | None = None,
):
    listings = available_listings(db, exclude_seller_id)
    if not listings:
        return []

    favourite_counts = dict(
        db.execute(
            select(Favourite.listing_id, func.count())
            .group_by(Favourite.listing_id)
        ).all()
    )

    reservation_counts = dict(
        db.execute(
            select(Reservation.listing_id, func.count())
            .where(Reservation.status == "completed")
            .group_by(Reservation.listing_id)
        ).all()
    )

    listings.sort(
        key=lambda item: (
            favourite_counts.get(item.id, 0)
            + 2 * reservation_counts.get(item.id, 0),
            item.created_at,
        ),
        reverse=True,
    )

    results = [
        {
            "listing": item,
            "score": None,
            "reason": "Popular among campus users",
        }
        for item in listings
    ]
    return results if limit is None else results[:limit]


def similar_recommendations(
    db: Session,
    listing_id: int,
    limit: int | None = 10,
):
    source = db.scalar(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.status == "available",
            Listing.hidden_at.is_(None),
            Listing.removed_at.is_(None),
        )
    )

    if source is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    source_vector = get_listing_embedding(db, source)
    candidates = available_listings(db)

    results = []
    for candidate in candidates:
        if candidate.id == source.id:
            continue

        vector = get_listing_embedding(db, candidate)
        score = cosine_similarity(source_vector, vector)

        results.append({
            "listing": candidate,
            "score": score,
            "reason": "Similar title, description and category",
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results if limit is None else results[:limit]


def personalized_recommendations(
    db: Session,
    user_id: int,
    limit: int | None = 10,
):
    favourite_ids = list(
        db.scalars(
            select(Favourite.listing_id).where(
                Favourite.user_id == user_id
            )
        ).all()
    )

    completed_ids = list(
        db.scalars(
            select(Reservation.listing_id).where(
                Reservation.buyer_id == user_id,
                Reservation.status == "completed",
            )
        ).all()
    )

    interest_ids = list(dict.fromkeys(favourite_ids + completed_ids))

    if not interest_ids:
        return popular_recommendations(
            db,
            limit=limit,
            exclude_seller_id=user_id,
        )

    interests = db.scalars(
        select(Listing).where(Listing.id.in_(interest_ids))
    ).all()

    if not interests:
        return popular_recommendations(
            db,
            limit=limit,
            exclude_seller_id=user_id,
        )

    vectors = [get_listing_embedding(db, item) for item in interests]

    # All vectors in a profile must come from the same embedding space.
    dimension = len(vectors[0])
    if any(len(vector) != dimension for vector in vectors):
        raise ValueError("Inconsistent embedding dimensions in user profile.")

    profile = [
        sum(vector[index] for vector in vectors) / len(vectors)
        for index in range(dimension)
    ]

    candidates = available_listings(db, exclude_seller_id=user_id)
    results = []

    for candidate in candidates:
        if candidate.id in interest_ids:
            continue

        vector = get_listing_embedding(db, candidate)
        score = cosine_similarity(profile, vector)

        results.append({
            "listing": candidate,
            "score": score,
            "reason": "Based on your favourites and completed reservations",
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results if limit is None else results[:limit]
