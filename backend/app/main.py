import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sakhi_ai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🌸 Sakhi AI Backend is starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    try:
        from app.database.database import log_ssl_startup_diagnostic
        log_ssl_startup_diagnostic()
    except Exception as e:
        logger.warning(f"Could not execute database SSL startup diagnostic: {e}")
    yield
    logger.info("🌸 Sakhi AI Backend shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-quality voice-first Telugu AI Companion API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Friendly Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Oops 😅 Something went wrong on my side. Please try again in a moment.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

# Safe Health Check (Never exposes passwords, keys, or internal credentials)
@app.get("/health", tags=["System"])
async def health_check():
    db_status = "untested"
    try:
        from app.database.database import check_db_connection
        is_connected = check_db_connection()
        db_status = "connected" if is_connected else "disconnected"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "disconnected"

    return {
        "status": "ok",
        "service": "Sakhi AI Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to Sakhi AI — Your Telugu AI Friend who listens, talks and stays with you. 🌸",
        "docs": "/docs",
        "health": "/health"
    }

# Include API routers
from app.api import auth, users, friend, chat, conversations, memories, voice

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(friend.router, prefix="/api/friend", tags=["Friend Profile"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(memories.router, prefix="/api/memories", tags=["Memories"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
