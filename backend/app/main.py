"""
Main FastAPI application with routing, middleware, and lifecycle management.
Excel AI Chatbot Backend API
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .api.v1 import chat, etl, file_deletion, files
from .core.config import settings
from .core.database import close_database, init_database
from .services.vanna_service import vanna_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Excel AI Chatbot API...")

    try:
        # Initialize database connections
        await init_database()
        logger.info("Database initialized")

        # Initialize vanna.ai service
        await vanna_service.initialize()
        logger.info("Vanna.ai service initialized")

        logger.info("Application startup completed")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Excel AI Chatbot API...")

    try:
        # Close database connections
        await close_database()
        logger.info("Database connections closed")

        logger.info("Application shutdown completed")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=settings.description,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.supabase.co", "*.zeabur.app", "localhost", "127.0.0.1"]
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing."""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} - "
        f"Processed in {process_time:.3f}s"
    )

    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred" if not settings.debug else str(exc),
            "request_id": id(request)
        }
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": id(request)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.version,
        "environment": settings.environment
    }


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": "/docs" if settings.debug else "Documentation not available",
        "health": "/health"
    }


# API Routes
app.include_router(chat.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(etl.router, prefix="/api/v1")
app.include_router(file_deletion.router, prefix="/api/v1")


# Development utilities
if settings.debug:

    @app.get("/debug/config")
    async def debug_config():
        """Debug endpoint to check configuration (development only)."""
        return {
            "app_name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "debug": settings.debug,
            "cors_origins": settings.cors_origins,
            "statement_timeout_ms": settings.statement_timeout_ms,
            "default_query_limit": settings.default_query_limit,
            "max_file_size_mb": settings.max_file_size_mb,
        }

    @app.get("/debug/database")
    async def debug_database():
        """Debug endpoint to test database connection (development only)."""
        from .core.database import db_manager

        try:
            is_healthy = await db_manager.test_connection()
            return {
                "database_healthy": is_healthy,
                "supabase_url": settings.supabase_url,
                "connection_status": "connected" if is_healthy else "disconnected"
            }
        except Exception as e:
            return {
                "database_healthy": False,
                "error": str(e),
                "connection_status": "error"
            }

    @app.get("/debug/vanna")
    async def debug_vanna():
        """Debug endpoint to test vanna.ai service (development only)."""
        try:
            # Test basic vanna functionality
            test_sql = await vanna_service.generate_sql(
                "SELECT COUNT(*) FROM test_table LIMIT 1"
            )

            return {
                "vanna_healthy": True,
                "model_name": settings.vanna_model_name,
                "test_sql": test_sql,
                "status": "connected"
            }
        except Exception as e:
            return {
                "vanna_healthy": False,
                "error": str(e),
                "status": "error"
            }


# Add startup banner
@app.on_event("startup")
async def startup_banner():
    """Print startup banner."""
    banner = f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║               Excel AI Chatbot Backend API                   ║
    ║                       Version {settings.version}                        ║
    ║                                                              ║
    ║  Environment: {settings.environment:<10} | Debug: {str(settings.debug):<5}           ║
    ║  Port: 8000                  | Docs: {'/docs' if settings.debug else 'Disabled':<10}        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    logger.info(banner)


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
