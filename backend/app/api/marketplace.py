from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.marketplace import (
    CategoryResponse,
    ListingCreate,
    ListingImageResponse,
    ListingResponse,
    ListingUpdate,
)
from app.services.marketplace import (
    create_listing,
    get_listing,
    list_categories,
    search_listings,
    update_listing,
)

router = APIRouter(tags=["Marketplace"])


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return list_categories(db)


@router.post(
    "/listings",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_listing(
        db,
        current_user,
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        condition=payload.condition,
    )


@router.get("/listings", response_model=list[ListingResponse])
def get_listings(
    q: str | None = Query(default=None, max_length=200),
    category_id: int | None = Query(default=None, gt=0),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    condition: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return search_listings(
        db,
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        limit=limit,
        offset=offset,
    )


@router.get("/listings/{listing_id}", response_model=ListingResponse)
def get_listing_details(
    listing_id: int,
    db: Session = Depends(get_db),
):
    return get_listing(db, listing_id)


@router.patch(
    "/listings/{listing_id}",
    response_model=ListingResponse,
)
def patch_listing(
    listing_id: int,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_listing(
        db,
        current_user,
        listing_id,
        payload.model_dump(exclude_unset=True),
    )


@router.post(
    "/listings/{listing_id}/favourite",
    response_model=ListingResponse,
)
def favourite_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.marketplace import add_favourite

    return add_favourite(db, current_user, listing_id)


@router.delete(
    "/listings/{listing_id}/favourite",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unfavourite_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.marketplace import remove_favourite

    remove_favourite(db, current_user, listing_id)


@router.get("/favourites", response_model=list[ListingResponse])
def get_my_favourites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.marketplace import list_favourites

    return list_favourites(db, current_user)

@router.post(
    "/listings/{listing_id}/images",
    response_model=ListingImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_listing_image_endpoint(
    listing_id: int,
    file: UploadFile = File(...),
    alt_text: str | None = Form(default=None, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.listing_images import upload_listing_image

    return await upload_listing_image(
        db=db,
        seller=current_user,
        listing_id=listing_id,
        file=file,
        alt_text=alt_text,
    )


@router.get(
    "/listings/{listing_id}/images",
    response_model=list[ListingImageResponse],
)
def get_listing_images_endpoint(
    listing_id: int,
    db: Session = Depends(get_db),
):
    from app.services.listing_images import list_listing_images

    return list_listing_images(db, listing_id)


@router.delete(
    "/listings/{listing_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_listing_image_endpoint(
    listing_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.listing_images import delete_listing_image

    delete_listing_image(
        db=db,
        seller=current_user,
        listing_id=listing_id,
        image_id=image_id,
    )