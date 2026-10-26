from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Category, Listing, User


def list_categories(db: Session) -> list[Category]:
    statement = (
        select(Category)
        .where(Category.is_active.is_(True))
        .order_by(Category.name.asc())
    )
    return list(db.scalars(statement).all())


def get_active_category(db: Session, category_id: int) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
        )
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Category not found or inactive",
        )

    return category


def create_listing(
    db: Session,
    seller: User,
    *,
    category_id: int,
    title: str,
    description: str,
    price: Decimal,
    condition: str,
) -> Listing:
    get_active_category(db, category_id)

    listing = Listing(
        seller_id=seller.id,
        category_id=category_id,
        title=title.strip(),
        description=description.strip(),
        price=price,
        currency="INR",
        condition=condition.strip(),
        status="available",
    )

    if not listing.title or not listing.description or not listing.condition:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Title, description, and condition cannot be blank",
        )

    db.add(listing)

    try:
        db.commit()
        db.refresh(listing)
    except Exception:
        db.rollback()
        raise

    return listing


def search_listings(
    db: Session,
    *,
    q: str | None = None,
    category_id: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    condition: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Listing]:
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_price cannot exceed max_price",
        )

    statement = select(Listing).where(
        Listing.status == "available",
        Listing.hidden_at.is_(None),
        Listing.removed_at.is_(None),
    )

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                Listing.title.ilike(pattern),
                Listing.description.ilike(pattern),
            )
        )

    if category_id is not None:
        statement = statement.where(Listing.category_id == category_id)

    if min_price is not None:
        statement = statement.where(Listing.price >= min_price)

    if max_price is not None:
        statement = statement.where(Listing.price <= max_price)

    if condition and condition.strip():
        statement = statement.where(
            Listing.condition == condition.strip()
        )

    statement = (
        statement
        .order_by(Listing.created_at.desc(), Listing.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def get_listing(
    db: Session,
    listing_id: int,
    *,
    include_unavailable: bool = False,
) -> Listing:
    statement = select(Listing).where(
        Listing.id == listing_id,
        Listing.hidden_at.is_(None),
        Listing.removed_at.is_(None),
    )

    if not include_unavailable:
        statement = statement.where(Listing.status == "available")

    listing = db.scalar(statement)

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    return listing


def update_listing(
    db: Session,
    seller: User,
    listing_id: int,
    changes: dict,
) -> Listing:
    listing = db.scalar(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.hidden_at.is_(None),
            Listing.removed_at.is_(None),
        )
    )

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    if listing.seller_id != seller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit another seller's listing",
        )

    if listing.status != "available":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only available listings can be edited",
        )

    changes = {
        key: value
        for key, value in changes.items()
        if value is not None
    }

    if "category_id" in changes:
        get_active_category(db, changes["category_id"])

    for field in ("title", "description", "condition"):
        if field in changes:
            changes[field] = changes[field].strip()
            if not changes[field]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"{field} cannot be blank",
                )

    for field, value in changes.items():
        setattr(listing, field, value)

    try:
        db.commit()
        db.refresh(listing)
    except Exception:
        db.rollback()
        raise

    return listing


def add_favourite(db: Session, user: User, listing_id: int):
    from app.models import Favourite

    listing = get_listing(db, listing_id)

    existing = db.get(Favourite, (user.id, listing.id))
    if existing is not None:
        # Repeated requests do not create duplicate favourites.
        return listing

    favourite = Favourite(
        user_id=user.id,
        listing_id=listing.id,
    )
    db.add(favourite)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return listing


def remove_favourite(db: Session, user: User, listing_id: int) -> None:
    from app.models import Favourite

    favourite = db.get(Favourite, (user.id, listing_id))

    if favourite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favourite not found",
        )

    db.delete(favourite)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_favourites(db: Session, user: User) -> list[Listing]:
    from app.models import Favourite

    statement = (
        select(Listing)
        .join(Favourite, Favourite.listing_id == Listing.id)
        .where(
            Favourite.user_id == user.id,
            Listing.status == "available",
            Listing.hidden_at.is_(None),
            Listing.removed_at.is_(None),
        )
        .order_by(Favourite.created_at.desc(), Listing.id.desc())
    )

    return list(db.scalars(statement).all())
