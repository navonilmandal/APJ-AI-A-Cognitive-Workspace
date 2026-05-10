import os
import sys
from pathlib import Path

# Add project root to sys.path for direct script execution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Cognitive AI Assistant API",
        description="Scalable backend for a memory-centric AI intelligence platform.",
        version="2.0.0",
        debug=settings.DEBUG
    )
    print("[HEARTBEAT] Server started/reloaded")

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup_event():
        logger.info("Cognitive Assistant V2 starting up...")
        # Ensure directories are ready
        settings.PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

    @app.get("/")
    async def root():
        return {
            "name": "Cognitive AI Assistant",
            "version": "2.0.0",
            "status": "online"
        }

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
