"""Main FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError

from backend.config import config
from backend.database import init_database
from backend.services.scanner import scan_library
from backend.services.watcher import start_watcher, stop_watcher

# Import API routers
from backend.api import albums, folders, photos, recycle_bin, search, tags


# Global scan status
scan_status = {"running": False, "progress": None}


async def background_scan():
    """Run library scan in background without blocking startup."""
    global scan_status
    print("Starting background library scan...")
    scan_status["running"] = True
    scan_status["progress"] = "Initializing..."
    
    await asyncio.sleep(2)  # Give app time to start
    try:
        scan_status["progress"] = "Scanning..."
        stats = scan_library()
        scan_status["running"] = False
        scan_status["progress"] = f"Complete: {stats}"
        print(f"Background scan complete: {stats}")
    except Exception as e:
        scan_status["running"] = False
        scan_status["progress"] = f"Error: {str(e)}"
        print(f"Background scan error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting photo manager application...")

    # Ensure required directories exist
    config.ensure_directories()

    # Initialize database
    init_database()
    print("Database initialized")

    # Run initial scan in background if configured
    if config.SCAN_ON_STARTUP:
        asyncio.create_task(background_scan())
        print("Background scan scheduled")

    # Start filesystem watcher if configured
    if config.AUTO_WATCH:
        start_watcher()
        print("Filesystem watcher started")

    yield

    # Shutdown
    print("Shutting down photo manager application...")
    stop_watcher()


# Create FastAPI app
app = FastAPI(
    title="Photo Manager",
    description="Lightweight photo management application",
    version="1.0.0",
    lifespan=lifespan
)

# Add session middleware for authentication
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    same_site="lax",  # "lax" is required to allow OAuth callback
    https_only=True
)

# Initialize OAuth for OIDC
oauth = OAuth()
if config.OIDC_CLIENT_ID:
    oauth.register(
        'oidc',
        client_id=config.OIDC_CLIENT_ID,
        client_secret=config.OIDC_CLIENT_SECRET,
        server_metadata_url=config.OIDC_DISCOVERY_URL,
        client_kwargs={'scope': 'openid profile email'}
    )


# Authentication dependency
def auth(request: Request) -> bool:
    """Check if user is authenticated via OIDC session or DEV_MODE."""
    if not config.OIDC_CLIENT_ID and not config.DEV_MODE:
        raise HTTPException(401, "Authentication required - OIDC not configured")
    return config.DEV_MODE or request.session.get('user') is not None


# Authentication endpoints
@app.get("/auth/login")
async def login(request: Request):
    """Redirect to OIDC provider for authentication."""
    if not config.OIDC_CLIENT_ID:
        raise HTTPException(400, "OIDC not configured")
    return await oauth.oidc.authorize_redirect(request, config.OIDC_REDIRECT_URI)


@app.get("/auth/callback")
async def callback(request: Request):
    """Handle OIDC callback and establish session."""
    try:
        token = await oauth.oidc.authorize_access_token(request)
        request.session['user'] = token.get('userinfo')
        return RedirectResponse("/")
    except OAuthError as e:
        logging.warning(f"OAuth error during callback: {type(e).__name__}")
        raise HTTPException(400, "Authentication failed")
    except Exception as e:
        logging.error(f"Unexpected error during auth callback: {type(e).__name__}")
        raise HTTPException(500, "Authentication service temporarily unavailable")


@app.post("/auth/logout")
async def logout(request: Request):
    """Clear user session."""
    request.session.clear()
    return {"ok": True}


@app.get("/auth/me")
async def me(request: Request):
    """Check authentication status."""
    return {"authenticated": auth(request)}

# Include API routers
app.include_router(photos.router)
app.include_router(folders.router)
app.include_router(albums.router)
app.include_router(tags.router)
app.include_router(search.router)
app.include_router(recycle_bin.router)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static"
)


# Serve index.html for root path
@app.get("/")
async def root():
    """Serve the main application page."""
    # Always serve index.html - it handles auth check on the frontend
    return FileResponse("frontend/templates/index.html")


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "scan_running": scan_status["running"],
        "scan_progress": scan_status["progress"]
    }


# Stats endpoint
@app.get("/api/stats")
async def get_stats(authenticated: bool = Depends(auth)):
    """Get library statistics."""
    if not authenticated:
        raise HTTPException(401, "Authentication required")

    from backend.database import get_db

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM photos WHERE deleted_at IS NULL")
        photo_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM albums")
        album_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM tags")
        tag_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM photos WHERE deleted_at IS NOT NULL")
        recycle_bin_count = cursor.fetchone()["count"]

        cursor.execute("SELECT SUM(file_size) as total FROM photos WHERE deleted_at IS NULL")
        total_size = cursor.fetchone()["total"] or 0

    return {
        "photos": photo_count,
        "albums": album_count,
        "tags": tag_count,
        "recycle_bin": recycle_bin_count,
        "total_size_bytes": total_size
    }
