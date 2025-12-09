"""
FastAPI application entry point.

This module initializes the FastAPI application with all necessary
configurations, middleware, and route handlers.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.db.session import init_db, close_db
from app.api import routes


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    Initializes database connections on startup and closes them on shutdown.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Code Review Agent Engine...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Code Review Agent Engine...")
    await close_db()
    logger.info("Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A workflow engine for executing agent-based code review processes with loop support",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.debug
)


# Include API routes
app.include_router(routes.router, prefix="/api/v1")


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """
    Root endpoint for health check.
    
    Returns:
        dict[str, str]: System status and application name
    """
    return {
        "status": "active",
        "message": f"{settings.app_name} is running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """
    Detailed health check endpoint.
    
    Returns:
        dict[str, str]: Detailed system health information
    """
    return {
        "status": "healthy",
        "database": "connected",
        "service": settings.app_name
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
