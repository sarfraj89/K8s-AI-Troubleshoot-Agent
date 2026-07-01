from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()

@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-kubernetes-agent",
        "mode": "demo" if settings.DEMO_MODE else "local",
        "demo_mode": settings.DEMO_MODE,
        "kubeconfig": settings.kubeconfig,
    }
