"""Insert repeatable synthetic demo data for ReUse Campus."""

from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Category, Listing, User
from app.services.auth import hash_password


USERS = [
    {
        "email": "demo.seller@reusecampus.test",
        "username": "demo_seller",
        "password": "DemoSeller2026!",
        "full_name": "Demo Seller",
        "student_id": "DEMO-SELLER-001",
    },
    {
        "email": "demo.buyer@reusecampus.test",
        "username": "demo_buyer",
        "password": "DemoBuyer2026!",
        "full_name": "Demo Buyer",
        "student_id": "DEMO-BUYER-001",
    },
]

CATEGORY_NAMES = [
    "Books",
    "Electronics",
    "Furniture",
    "Clothing",
    "Stationery",
]

LISTINGS = [
    {
        "title": "Data Structures Textbook",
        "description": "Synthetic demo listing for a used data structures textbook.",
        "price": Decimal("250.00"),
        "condition": "good",
        "category": "Books",
    },
    {
        "title": "Scientific Calculator",
        "description": "Synthetic demo listing for a scientific calculator.",
        "price": Decimal("350.00"),
        "condition": "good",
        "category": "Electronics",
    },
    {
        "title": "Study Desk",
        "description": "Synthetic demo listing for a compact study desk.",
        "price": Decimal("900.00"),
        "condition": "used",
        "category": "Furniture",
    },
]


def seed() -> None:
    with SessionLocal() as db:
        # Create categories first so listing foreign keys can reference them.
        categories = {}
        for name in CATEGORY_NAMES:
            category = db.scalar(
                select(Category).where(Category.name == name)
            )
            if category is None:
                category = Category(name=name, is_active=True)
                db.add(category)
                db.flush()
            categories[name] = category

        # Reuse existing demo users. Never overwrite existing credentials.
        users = {}
        for data in USERS:
            user = db.scalar(
                select(User).where(User.username == data["username"])
            )

            if user is None:
                user = db.scalar(
                    select(User).where(User.email == data["email"])
                )

            if user is None:
                user = User(
                    email=data["email"],
                    username=data["username"],
                    password_hash=hash_password(data["password"]),
                    full_name=data["full_name"],
                    student_id=data["student_id"],
                    verification_status="pending",
                    role="student",
                    account_status="active",
                )
                db.add(user)
                db.flush()

            users[data["username"]] = user

        seller = users["demo_seller"]

        # A title is used as the seed's stable identifier.
        for data in LISTINGS:
            listing = db.scalar(
                select(Listing).where(
                    Listing.seller_id == seller.id,
                    Listing.title == data["title"],
                )
            )

            if listing is None:
                db.add(
                    Listing(
                        seller_id=seller.id,
                        category_id=categories[data["category"]].id,
                        title=data["title"],
                        description=data["description"],
                        price=data["price"],
                        currency="INR",
                        condition=data["condition"],
                        status="available",
                    )
                )

        db.commit()

        print(
            "Seed complete:",
            f"{len(CATEGORY_NAMES)} demo categories,",
            f"{len(USERS)} demo users,",
            f"{len(LISTINGS)} demo listings defined.",
        )


if __name__ == "__main__":
    seed()
