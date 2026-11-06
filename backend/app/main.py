
from pathlib import Path

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth import router as auth_router
from app.api.enquiries import router as enquiries_router
from app.api.marketplace import router as marketplace_router
from app.api.moderation import (
    moderation_router,
    reports_router,
)
from app.api.recommendations import router as recommendations_router
from app.api.reservations import router as reservations_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for the ReUse Campus "
        "student-to-student marketplace with AI-powered recommendations."
    ),
)
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads",
)

app.include_router(reservations_router)
app.include_router(enquiries_router)
app.include_router(reports_router)
app.include_router(moderation_router)
app.include_router(recommendations_router)
app.include_router(marketplace_router)
app.include_router(auth_router)




def error_body(code: str, message: str, details=None):
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


async def http_error(request, exc: StarletteHTTPException):
    detail = exc.detail

    if isinstance(detail, dict):
        code = detail.get("code", f"HTTP_{exc.status_code}")
        message = detail.get("message", "Request failed")
    else:
        code = f"HTTP_{exc.status_code}"
        message = str(detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(code, message),
        headers=exc.headers,
    )


async def validation_error(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_body(
            "VALIDATION_ERROR",
            "Invalid input",
            jsonable_encoder(exc.errors()),
        ),
    )


app.add_exception_handler(StarletteHTTPException, http_error)
app.add_exception_handler(RequestValidationError, validation_error)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
    }
