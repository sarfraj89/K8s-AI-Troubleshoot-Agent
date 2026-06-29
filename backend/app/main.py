from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import health, investigate
from app.core.config import settings
from app.kubernetes.kubeconfig_sync import sync_kubeconfig

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Kubernetes Agent API",
        version="0.1.0",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
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
        sync_kubeconfig()

    return app

app = create_app()
