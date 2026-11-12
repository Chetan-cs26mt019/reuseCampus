from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import (
    TOKEN_LIFETIME_SECONDS,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class PasswordConfirmation(BaseModel):
    password: str = Field(min_length=1, max_length=128)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = str(data.email).strip().lower()
    username = data.username.strip()

    existing = db.scalar(
        select(User).where(
            or_(User.email == email, User.username == username)
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered",
        )

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        student_id=data.student_id,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=TOKEN_LIFETIME_SECONDS,
        user=user,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    identifier = data.username_or_email.strip()

    user = db.scalar(
        select(User).where(
            or_(
                User.email == identifier.lower(),
                User.username == identifier,
            )
        )
    )

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=TOKEN_LIFETIME_SECONDS,
        user=user,
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    data: PasswordConfirmation,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Deactivate and anonymise the account while preserving marketplace history."""
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Password is incorrect")

    from datetime import UTC, datetime

    from app.models import Listing

    stamp = datetime.now(UTC).replace(tzinfo=None).timestamp()
    user.email = f"deleted-{user.id}-{int(stamp)}@deleted.invalid"
    user.username = f"deleted_{user.id}_{int(stamp)}"
    user.full_name = "Deleted User"
    user.student_id = None
    user.password_hash = hash_password(__import__("secrets").token_urlsafe(32))
    user.account_status = "deleted"
    for listing in db.scalars(select(Listing).where(Listing.seller_id == user.id)):
        if listing.status != "removed":
            listing.status = "removed"
            listing.removed_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
