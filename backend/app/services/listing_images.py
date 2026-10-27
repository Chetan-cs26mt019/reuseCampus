from io import BytesIO
from pathlib import Path
import warnings
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Listing, ListingImage, User


BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "uploads" / "listings"

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGES_PER_LISTING = 5

# Content signatures are checked instead of trusting the supplied filename
# or Content-Type header.
IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
    "image/gif": (b"GIF87a", ".gif"),
    "image/webp": (b"RIFF", ".webp"),
}


def detect_image_type(data: bytes) -> tuple[str, str] | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"

    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", ".gif"

    if (
        len(data) >= 12
        and data.startswith(b"RIFF")
        and data[8:12] == b"WEBP"
    ):
        return "image/webp", ".webp"

    return None


def get_owned_listing(
    db: Session,
    seller: User,
    listing_id: int,
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
            detail="You cannot manage images for another seller's listing",
        )

    if listing.status != "available":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Images can only be changed on available listings",
        )

    return listing


async def upload_listing_image(
    db: Session,
    seller: User,
    listing_id: int,
    file: UploadFile,
    alt_text: str | None = None,
) -> ListingImage:
    # Check ownership before accepting the file.
    listing = get_owned_listing(db, seller, listing_id)

    image_count = db.scalar(
        select(func.count())
        .select_from(ListingImage)
        .where(ListingImage.listing_id == listing.id)
    )

    if image_count >= MAX_IMAGES_PER_LISTING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A listing can have at most {MAX_IMAGES_PER_LISTING} images",
        )

    # Read at most one byte beyond the limit to detect oversized uploads.
    data = await file.read(MAX_IMAGE_SIZE + 1)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The uploaded file is empty",
        )

    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image must be 5 MB or smaller",
        )

    detected = detect_image_type(data)

    if detected is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, GIF, and WebP images are accepted",
        )

    mime_type, extension = detected
    supported_formats = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "GIF": "image/gif",
        "WEBP": "image/webp",
    }

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)

            with Image.open(BytesIO(data)) as decoded:
                actual_format = decoded.format
                width, height = decoded.size
                decoded.verify()

            if width * height > 25_000_000:
                raise ValueError("Image dimensions are too large")

            if supported_formats.get(actual_format) != mime_type:
                raise ValueError("Image content does not match its signature")

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file is not a valid supported image",
        ) from exc

    # Ignore the client-supplied filename. Generate a unique safe name.
    filename = f"{uuid4().hex}{extension}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    disk_path = UPLOAD_DIR / filename

    # Use the next available position. The unique database constraint
    # remains the final guard if simultaneous uploads race.
    next_position = db.scalar(
        select(func.max(ListingImage.position)).where(
            ListingImage.listing_id == listing.id
        )
    )
    position = 0 if next_position is None else next_position + 1

    image = ListingImage(
        listing_id=listing.id,
        image_url=f"/uploads/listings/{filename}",
        alt_text=alt_text.strip()[:255] if alt_text and alt_text.strip() else None,
        position=position,
    )

    try:
        disk_path.write_bytes(data)
        db.add(image)
        db.commit()
        db.refresh(image)
        return image
    except Exception:
        db.rollback()
        disk_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


def list_listing_images(
    db: Session,
    listing_id: int,
) -> list[ListingImage]:
    # Publicly show images only for publicly available listings.
    listing = db.scalar(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.status == "available",
            Listing.hidden_at.is_(None),
            Listing.removed_at.is_(None),
        )
    )

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    statement = (
        select(ListingImage)
        .where(ListingImage.listing_id == listing_id)
        .order_by(ListingImage.position.asc(), ListingImage.id.asc())
    )
    return list(db.scalars(statement).all())


def delete_listing_image(
    db: Session,
    seller: User,
    listing_id: int,
    image_id: int,
) -> None:
    get_owned_listing(db, seller, listing_id)

    image = db.scalar(
        select(ListingImage).where(
            ListingImage.id == image_id,
            ListingImage.listing_id == listing_id,
        )
    )

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    # Resolve the stored URL's generated filename safely. Never accept
    # a filesystem path from the client.
    filename = Path(image.image_url).name
    disk_path = UPLOAD_DIR / filename

    try:
        db.delete(image)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Delete the file only after the database deletion succeeds.
    disk_path.unlink(missing_ok=True)
