from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import health, investigate
from app.core.config import settings
from app.kubernetes.kubeconfig_sync import sync_kubeconfig


def _allowed_origins() -> list[str]:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if settings.FRONTEND_URL:
        origins.append(settings.FRONTEND_URL.rstrip("/"))
    return origins

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Kubernetes Agent API",
        version="0.1.0",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(investigate.router, tags=["investigation"])

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting AI Kubernetes Agent API...")
        if settings.DEMO_MODE:
            logger.info("Demo mode enabled; skipping kubeconfig sync")
            return
        sync_kubeconfig()

    return app

app = create_app()
