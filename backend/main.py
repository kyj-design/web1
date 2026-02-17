"""
Canva-Etsy Automation System - FastAPI Backend
Main application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from .config import settings
from .database import init_db

# Create FastAPI app
app = FastAPI(
    title="Canva-Etsy Automation API",
    description="Automate Canva template listing to Etsy with market research and SEO optimization",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
_allowed_origins = [settings.frontend_url]
if settings.frontend_url != "http://localhost:3000":
    _allowed_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Create upload directories if they don't exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.pdf_dir).mkdir(parents=True, exist_ok=True)
Path(settings.image_dir).mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    # Mask credentials in DB URL for safe logging
    _db_url = settings.database_url
    if "@" in _db_url:
        _db_url = _db_url.split("@")[-1]
        _db_url = f"...@{_db_url}"
    print("✅ Database initialized")
    print(f"📊 Database: {_db_url}")
    print(f"🤖 LLM Provider: {settings.llm_provider}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Canva-Etsy Automation API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected" if settings.database_url else "not configured",
        "llm_provider": settings.llm_provider,
        "etsy_api": "configured" if settings.etsy_api_key else "not configured"
    }


# Phase 2: Market Research & Bestseller Analysis routers
from .routers import market, bestsellers, templates, listings, auth
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(bestsellers.router, prefix="/api/bestsellers", tags=["bestsellers"])

# Phase 3: Template Management & PDF Generation
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])

# Phase 4: SEO Optimization & Etsy Listings
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])

# Phase 5: Etsy OAuth 2.0 Authentication
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


if __name__ == "__main__":
    import uvicorn
    _host = os.environ.get("APP_HOST", "127.0.0.1")
    _port = int(os.environ.get("APP_PORT", "8000"))
    _reload = os.environ.get("APP_ENV", "production") == "development"
    uvicorn.run(
        "backend.main:app",
        host=_host,
        port=_port,
        reload=_reload,
        log_level=settings.log_level.lower()
    )
