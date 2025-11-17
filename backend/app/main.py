"""
Main FastAPI application.

Face Recognition and Document Analysis System with OCR.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time
from .config import settings
from .database import init_db
from .routes import auth_router, documents_router, search_router, admin_router
from .utils.logging import setup_logging

# Setup logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Face Recognition & OCR System",
    description="Automated face recognition and document analysis system with OCR",
    version="1.0.0",
    docs_url="/docs" if settings.is_debug else None,  # Disable in production
    redoc_url="/redoc" if settings.is_debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} - {request.url.path} - {process_time:.3f}s"
    )

    # Add custom header
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=settings.is_debug)

    if settings.is_debug:
        # Show detailed error in debug mode
        import traceback
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "traceback": traceback.format_exc()
            },
        )
    else:
        # Generic error in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


# Include routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(search_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Face Recognition & OCR System",
        "version": "1.0.0",
        "mode": settings.MODE,
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    # Check database
    try:
        from .database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"

    # Check Elasticsearch
    try:
        from .services.elasticsearch_service import elasticsearch_service
        if elasticsearch_service.client and elasticsearch_service.client.ping():
            es_status = "ok"
        else:
            es_status = "error"
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        es_status = "error"

    # Check GPU availability
    gpu_status = "not_available"
    try:
        import torch
        if torch.cuda.is_available():
            gpu_status = f"available ({torch.cuda.get_device_name(0)})"
    except:
        pass

    # Overall status
    overall_status = "healthy" if db_status == "ok" and es_status == "ok" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "elasticsearch": es_status,
        "gpu": gpu_status,
        "mode": settings.MODE
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Face Recognition & OCR System")
    logger.info(f"Mode: {settings.MODE}")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Check Elasticsearch connection
    try:
        from .services.elasticsearch_service import elasticsearch_service
        if elasticsearch_service.client:
            logger.info("Elasticsearch connected")
        else:
            logger.warning("Elasticsearch not connected - search functionality will be limited")
    except Exception as e:
        logger.warning(f"Elasticsearch check failed: {e}")

    # Check CUDA/GPU availability
    try:
        import torch
        import os

        use_gpu = os.getenv('USE_GPU', 'false').lower() == 'true'

        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            cuda_version = torch.version.cuda
            logger.info(f"CUDA is available! GPU: {device_name}")
            logger.info(f"CUDA version: {cuda_version}")
            logger.info(f"PyTorch version: {torch.__version__}")

            if use_gpu:
                logger.info("GPU acceleration ENABLED")
            else:
                logger.warning("GPU available but USE_GPU=false - using CPU")
        else:
            if use_gpu:
                logger.warning("USE_GPU=true but CUDA is not available - falling back to CPU")
            else:
                logger.info("Running in CPU-only mode")

    except Exception as e:
        logger.warning(f"Cannot check CUDA status: {e}")

    logger.info("Application startup complete")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Face Recognition & OCR System")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_debug,
        log_level=settings.LOG_LEVEL.lower()
    )
