from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api import health, investigate
from app.core.config import settings
from app.kubernetes.kubeconfig_sync import sync_kubeconfig


def _allowed_origins() -> list[str]:
    origins = {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://k8s-ai-troubleshoot-agent.vercel.app",
    }
    if settings.FRONTEND_URL:
        origins.add(settings.FRONTEND_URL.rstrip("/"))
    if settings.CORS_ALLOWED_ORIGINS:
        origins.update(
            origin.strip().rstrip("/")
            for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        )
    return sorted(origins)

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

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request, exc: Exception):
        logger.exception("Unhandled API error: {}", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(exc)},
        )

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting AI Kubernetes Agent API...")
        if settings.DEMO_MODE:
            logger.info("Demo mode enabled; skipping kubeconfig sync")
            return
        sync_kubeconfig()

    return app

app = create_app()
