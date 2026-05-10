import os
import sys
from pathlib import Path

# Add project root to sys.path for direct script execution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from backend.api.routes import router
from backend.auth.routes import router as auth_router
from backend.core.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)

def create_app() -> FastAPI:
    # Set debug based on environment
    is_debug = settings.DEBUG and os.getenv("ENV", "development") != "production"
    
    app = FastAPI(
        title="Cognitive AI Assistant API",
        description="Hardened backend for a memory-centric AI intelligence platform.",
        version="2.0.0",
        debug=is_debug
    )
    
    # Security: Rate Limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Security: Trusted Host Middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", os.getenv("DOMAIN", "localhost")]
    )

    # Security: Hardened CORS
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup_event():
        logger.info("Cognitive Assistant V2 starting up with security hardening...")
        
        # Initialize Database
        from backend.auth.user_store import get_user_store, UserCreate, init_db
        db_ready = init_db()
        if not db_ready:
            logger.warning("PostgreSQL connection failed. Auth system may be unavailable.")
            
        # Ensure directories are ready
        settings.PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        # Security: Create security log if doesn't exist
        log_dir = settings.PROJECT_ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        (log_dir / "security.log").touch(exist_ok=True)
        
        # Security: Create default admin user for auditing if not exists
        try:
            store = get_user_store()
            if db_ready and not store.get_user("admin"):
                logger.info("Security: Creating default admin user")
                store.create_user(UserCreate(
                    username="admin", 
                    email="admin@apj-ai.com", 
                    password="apj_admin_password_2026"
                ))
        except Exception as e:
            logger.error(f"Failed to create/verify admin user: {e}")

    @app.get("/")
    @limiter.limit("5/minute")
    async def root(request: Request): # slowapi needs 'request' argument
        return {
            "name": "Cognitive AI Assistant",
            "version": "2.0.0",
            "status": "online",
            "security": "hardened"
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
