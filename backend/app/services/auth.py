import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from app.core.config import settings


_password_hasher = PasswordHasher()
TOKEN_LIFETIME_SECONDS = 3600


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether the password matches the stored hash."""
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, VerifyMismatchError):
        return False


def _secret_key() -> bytes:
    """Load a sufficiently strong signing key from the environment."""
    key = os.getenv("SECRET_KEY") or settings.secret_key

    if (
        not key
        or key == "development-only-change-this-key"
        or len(key) < 32
    ):
        raise RuntimeError(
            "Set a strong SECRET_KEY in backend/.env before using authentication"
        )

    return key.encode("utf-8")


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_access_token(user_id: int) -> str:
    """Create a signed token with an expiration time."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + TOKEN_LIFETIME_SECONDS,
        "jti": secrets.token_urlsafe(16),
    }

    header_part = _b64encode(
        json.dumps(header, separators=(",", ":")).encode()
    )
    payload_part = _b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    )
    signing_input = f"{header_part}.{payload_part}".encode("ascii")

    signature = hmac.new(
        _secret_key(), signing_input, hashlib.sha256
    ).digest()

    return f"{header_part}.{payload_part}.{_b64encode(signature)}"


def decode_access_token(token: str) -> int:
    """Validate a signed token and return its user ID."""
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}".encode("ascii")

        expected_signature = hmac.new(
            _secret_key(), signing_input, hashlib.sha256
        ).digest()
        supplied_signature = _b64decode(signature_part)

        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise ValueError("Invalid signature")

        header = json.loads(_b64decode(header_part))
        payload = json.loads(_b64decode(payload_part))

        if header != {"alg": "HS256", "typ": "JWT"}:
            raise ValueError("Unsupported token")

        if int(payload["exp"]) <= int(time.time()):
            raise ValueError("Token expired")

        user_id = int(payload["sub"])
        if user_id <= 0:
            raise ValueError("Invalid user ID")

        return user_id

    except (
        ValueError,
        TypeError,
        KeyError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        raise ValueError("Invalid or expired access token") from exc
