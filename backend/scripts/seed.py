"""Idempotent synthetic demo data for ReUse Campus presentations."""
import re
from decimal import Decimal
from html import escape
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Category, Listing, ListingImage, User
from app.services.auth import hash_password

# Local-demo credentials only. Never reuse these on a public deployment.
USERS = [
    {"email": "demo.seller@reusecampus.test", "username": "demo_seller", "password": "DemoSeller2026!", "full_name": "ReUse Campus Demo Seller", "student_id": "DEMO-SELLER-001", "role": "student"},
    {"email": "demo.buyer@reusecampus.test", "username": "demo_buyer", "password": "DemoBuyer2026!", "full_name": "ReUse Campus Demo Buyer", "student_id": "DEMO-BUYER-001", "role": "student"},
    {"email": "moderator@reusecampus.test", "username": "demo_moderator", "password": "DemoModerator2026!", "full_name": "ReUse Campus Moderator", "student_id": "DEMO-MOD-001", "role": "moderator"},
]
CATEGORY_NAMES = ["Books", "Electronics", "Furniture", "Clothing", "Stationery"]
# title, category, INR price, condition, description
PRODUCTS = [
    ('Textbook', 'Books', 250, 'good', 'A useful textbook for college coursework and revision.'),
    ('Notebook', 'Books', 80, 'good', 'Notebook for everyday class notes and practice.'),
    ('Story Book', 'Books', 120, 'good', 'A pre-loved story book for leisure reading.'),
    ('Maths Book', 'Books', 180, 'good', 'Mathematics textbook for concepts and exercises.'),
    ('Physics Book', 'Books', 200, 'good', 'Physics reference book for students.'),
    ('Chemistry Book', 'Books', 180, 'good', 'Chemistry textbook for coursework and revision.'),
    ('English Book', 'Books', 100, 'good', 'English learning and reference book.'),
    ('Programming Book', 'Books', 250, 'good', 'Programming reference for learning and practice.'),
    ('Exam Guide', 'Books', 150, 'good', 'Exam preparation guide with useful study material.'),
    ('Dictionary', 'Books', 120, 'good', 'Dictionary for vocabulary and language reference.'),
    ('Laptop', 'Electronics', 18000, 'good', 'Laptop suitable for study, projects and everyday work.'),
    ('Smartphone', 'Electronics', 5000, 'good', 'Smartphone for communication and everyday use.'),
    ('Tablet', 'Electronics', 6500, 'good', 'Tablet useful for reading and digital study.'),
    ('Keyboard', 'Electronics', 450, 'good', 'Keyboard for desktop or laptop use.'),
    ('Mouse', 'Electronics', 200, 'good', 'Computer mouse for everyday navigation.'),
    ('Headphones', 'Electronics', 500, 'good', 'Headphones for music, classes and calls.'),
    ('Earphones', 'Electronics', 180, 'good', 'Earphones for everyday listening.'),
    ('Calculator', 'Electronics', 250, 'good', 'Calculator for academic calculations.'),
    ('Power Bank', 'Electronics', 600, 'good', 'Portable power bank for charging devices.'),
    ('USB Cable', 'Electronics', 100, 'good', 'USB cable for charging and data transfer.'),
    ('Study Table', 'Furniture', 900, 'good', 'Study table for a home or hostel workspace.'),
    ('Office Chair', 'Furniture', 1200, 'good', 'Chair suitable for a study or work desk.'),
    ('Bookshelf', 'Furniture', 650, 'good', 'Bookshelf for organising books and supplies.'),
    ('Table Lamp', 'Furniture', 300, 'good', 'Table lamp for reading and studying.'),
    ('Bedside Table', 'Furniture', 450, 'good', 'Small table for bedside storage.'),
    ('Plastic Chair', 'Furniture', 250, 'good', 'Lightweight chair for everyday use.'),
    ('Laptop Stand', 'Furniture', 350, 'good', 'Stand for placing a laptop at a comfortable height.'),
    ('Shoe Rack', 'Furniture', 500, 'good', 'Rack for organising footwear.'),
    ('Storage Box', 'Furniture', 250, 'good', 'Storage box for keeping personal items organised.'),
    ('Wall Clock', 'Furniture', 180, 'good', 'Wall clock for a room or study space.'),
    ('T-Shirt', 'Clothing', 180, 'good', 'Casual T-shirt for everyday wear.'),
    ('Shirt', 'Clothing', 250, 'good', 'Shirt suitable for casual or formal use.'),
    ('Hoodie', 'Clothing', 350, 'good', 'Comfortable hoodie for everyday wear.'),
    ('Jacket', 'Clothing', 450, 'good', 'Jacket for daily use.'),
    ('Jeans', 'Clothing', 400, 'good', 'Jeans for casual everyday wear.'),
    ('Track Pants', 'Clothing', 220, 'good', 'Comfortable track pants.'),
    ('Sweater', 'Clothing', 300, 'good', 'Sweater for cooler weather.'),
    ('Backpack', 'Clothing', 500, 'good', 'Backpack for carrying books and essentials.'),
    ('Running Shoes', 'Clothing', 650, 'good', 'Shoes for running and everyday activity.'),
    ('Sandals', 'Clothing', 250, 'good', 'Sandals for everyday use.'),
    ('Pen Set', 'Stationery', 60, 'good', 'Set of pens for writing and note-taking.'),
    ('Pencil Box', 'Stationery', 80, 'good', 'Pencil box for organising stationery.'),
    ('Water Bottle', 'Stationery', 120, 'good', 'Reusable water bottle for daily use.'),
    ('Sticky Notes', 'Stationery', 60, 'good', 'Sticky notes for reminders and study notes.'),
    ('Highlighters', 'Stationery', 85, 'good', 'Highlighters for marking important information.'),
    ('Geometry Box', 'Stationery', 80, 'good', 'Geometry tools for academic work.'),
    ('File Folder', 'Stationery', 75, 'good', 'Folder for organising papers and documents.'),
    ('Paper Bundle', 'Stationery', 160, 'good', 'Paper bundle for assignments and printing.'),
    ('Drawing Book', 'Stationery', 100, 'good', 'Drawing book for sketches and practice.'),
    ('Ruler Set', 'Stationery', 50, 'good', 'Ruler set for drawing and measurements.'),
]
BACKEND_DIR = Path(__file__).resolve().parents[1]
DEMO_IMAGE_DIR = BACKEND_DIR / "uploads" / "demo"


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def make_placeholder(title: str, category: str, description: str, path: Path) -> None:
    """Write a small local SVG image labelled for the corresponding product."""
    title_text = escape(title[:34])
    category_text = escape(category.upper())
    description_text = escape(description[:62])
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" viewBox="0 0 900 650">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e0f2fe"/><stop offset="1" stop-color="#ede9fe"/></linearGradient></defs>
<rect width="900" height="650" rx="34" fill="url(#bg)"/><circle cx="450" cy="235" r="112" fill="#fff" opacity=".72"/><rect x="390" y="170" width="120" height="105" rx="12" fill="#64748b" opacity=".75"/><path d="M410 195h80M410 220h80M410 245h55" stroke="#fff" stroke-width="9" stroke-linecap="round"/>
<text x="450" y="410" text-anchor="middle" font-family="Arial,sans-serif" font-size="25" font-weight="700" letter-spacing="4" fill="#475569">{category_text}</text>
<text x="450" y="465" text-anchor="middle" font-family="Arial,sans-serif" font-size="34" font-weight="700" fill="#172554">{title_text}</text>
<text x="450" y="515" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" fill="#475569">{description_text}</text>
<text x="450" y="590" text-anchor="middle" font-family="Arial,sans-serif" font-size="17" fill="#64748b">REUSE CAMPUS - DEMO IMAGE</text></svg>'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def seed() -> None:
    with SessionLocal() as db:
        categories = {}
        for name in CATEGORY_NAMES:
            category = db.scalar(select(Category).where(Category.name == name))
            if category is None:
                category = Category(name=name, is_active=True)
                db.add(category)
                db.flush()
            categories[name] = category

        users = {}
        for data in USERS:
            user = db.scalar(select(User).where(User.username == data["username"]))
            if user is None:
                user = db.scalar(select(User).where(User.email == data["email"]))
            if user is None:
                user = User(
                    email=data["email"], username=data["username"],
                    password_hash=hash_password(data["password"]),
                    full_name=data["full_name"], student_id=data["student_id"],
                    verification_status="approved", role=data["role"],
                    account_status="active",
                )
                db.add(user)
                db.flush()
            elif data["role"] == "moderator":
                user.role = "moderator"
                user.account_status = "active"
                user.verification_status = "approved"
            users[data["username"]] = user

        # The seeded catalogue is owned by the single demo seller account.
        seller = users["demo_seller"]

        created = 0
        image_count = 0
        for index, (title, category_name, price, condition, description) in enumerate(PRODUCTS, start=1):
            listing = db.scalar(select(Listing).where(
                Listing.seller_id == seller.id, Listing.title == title
            ))
            if listing is None:
                listing = Listing(
                    seller_id=seller.id, category_id=categories[category_name].id,
                    title=title, description=description, price=Decimal(str(price)),
                    currency="INR", condition=condition, status="available",
                )
                db.add(listing)
                db.flush()
                created += 1
            else:
                # Keep the known demo catalogue consistent across seed runs.
                listing.category_id = categories[category_name].id
                listing.description = description
                listing.price = Decimal(str(price))
                listing.currency = "INR"
                listing.condition = condition
                if listing.removed_at is None and listing.hidden_at is None:
                    listing.status = "available"
            photo_filename = f"{index:02d}.jpg"
            photo_path = DEMO_IMAGE_DIR / photo_filename

            if photo_path.exists():
                filename = photo_filename
            else:
                filename = f"{slugify(title)}.svg"
                image_path = DEMO_IMAGE_DIR / filename
                if not image_path.exists():
                    make_placeholder(
                        title, category_name, description, image_path
                    )

            existing_image = db.scalar(select(ListingImage).where(
                ListingImage.listing_id == listing.id
            ).order_by(ListingImage.position).limit(1))

            if existing_image is None:
                db.add(ListingImage(
                    listing_id=listing.id,
                    image_url=f"/uploads/demo/{filename}",
                    alt_text=f"Demo product image for {title}", position=0,
                ))
                image_count += 1
        db.commit()
        print(
            f"Seed complete: {len(CATEGORY_NAMES)} categories; {len(USERS)} demo accounts; "
            f"{len(PRODUCTS)} catalogue products; {created} new listings; "
            f"{image_count} new local placeholder images."
        )
        print("All seeded catalogue listings belong to demo_seller; existing records are preserved.")


if __name__ == "__main__":
    seed()
