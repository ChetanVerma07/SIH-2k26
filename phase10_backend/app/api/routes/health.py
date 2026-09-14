from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "service": "passive-shelter-api",
        "version": settings.app_version,
    }
