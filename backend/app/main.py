from app.api.marketplace import router as marketplace_router
from fastapi import FastAPI
from app.api.enquiries import router as enquiries_router

from app.api.reservations import router as reservations_router
from app.core.config import settings
from app.api.moderation import (
    moderation_router,
    reports_router,
)
from app.api.chatbot import router as chatbot_router
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for the ReUse Campus "
        "student-to-student marketplace and chatbot."
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
app.include_router(chatbot_router)
app.include_router(marketplace_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
    }
