"""Promote an existing user to moderator. Run only by the project owner.

Usage: python scripts/promote_moderator.py user@example.edu
"""
import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import User


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/promote_moderator.py <registered-email>")

    email = sys.argv[1].strip().lower()
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            raise SystemExit("No registered user found with that email.")
        if user.account_status != "active":
            raise SystemExit("Cannot promote an inactive account.")
        user.role = "moderator"
        db.commit()
        print(f"Promoted {user.username} ({user.email}) to moderator.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
