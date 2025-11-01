"""Configuration module for photo manager."""

import os
import secrets
from pathlib import Path


class Config:
    """Application configuration loaded from environment variables."""

    # Paths
    PHOTOS_PATH: Path = Path(os.getenv("PHOTOS_PATH", "/photos"))
    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", "/app/data/metadata/photos.db"))
    THUMBNAIL_PATH: Path = Path(os.getenv("THUMBNAIL_PATH", "/app/data/cache/thumbnails"))

    # Performance settings
    THUMBNAIL_SIZE: int = int(os.getenv("THUMBNAIL_SIZE", "200"))
    THUMBNAIL_QUALITY: int = int(os.getenv("THUMBNAIL_QUALITY", "80"))

    # Behavior settings
    SCAN_ON_STARTUP: bool = os.getenv("SCAN_ON_STARTUP", "true").lower() == "true"
    AUTO_WATCH: bool = os.getenv("AUTO_WATCH", "true").lower() == "true"

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    # OIDC Authentication
    OIDC_CLIENT_ID: str = os.getenv("OIDC_CLIENT_ID", "")
    OIDC_CLIENT_SECRET: str = os.getenv("OIDC_CLIENT_SECRET", "")
    OIDC_DISCOVERY_URL: str = os.getenv("OIDC_DISCOVERY_URL", "")
    OIDC_REDIRECT_URI: str = os.getenv("OIDC_REDIRECT_URI", "http://localhost:8000/auth/callback")
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", secrets.token_hex(32))
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"

    # Supported image formats
    SUPPORTED_FORMATS = {
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".cr2", ".cr3", ".nef", ".arf", ".dng", ".orf", ".rw2", ".arw"
    }

    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist."""
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.THUMBNAIL_PATH.mkdir(parents=True, exist_ok=True)
        cls.PHOTOS_PATH.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
