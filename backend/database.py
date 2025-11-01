"""Database schema and connection management."""

import sqlite3
from contextlib import contextmanager
from typing import Generator

from backend.config import config


def get_connection() -> sqlite3.Connection:
    """
    Create a database connection.

    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(str(config.DATABASE_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Yields:
        SQLite connection object
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database schema and indexes."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Photos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id TEXT PRIMARY KEY,              -- SHA256 hash
                file_path TEXT NOT NULL,          -- Relative path from mounted dir
                filename TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                width INTEGER,
                height INTEGER,
                created_at TIMESTAMP,             -- From EXIF or file
                modified_at TIMESTAMP,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                thumbnail_path TEXT,
                deleted_at TIMESTAMP              -- Soft-delete timestamp
            )
        """)

        # Add deleted_at column if it doesn't exist (migration)
        cursor.execute("PRAGMA table_info(photos)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'deleted_at' not in columns:
            cursor.execute("ALTER TABLE photos ADD COLUMN deleted_at TIMESTAMP")

        # Albums table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Photo-Album junction (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_albums (
                photo_id TEXT,
                album_id TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (photo_id, album_id),
                FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
                FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
            )
        """)

        # Photo-Tag junction (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_tags (
                photo_id TEXT,
                tag_id TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (photo_id, tag_id),
                FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

        # Metadata table (EXIF data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                photo_id TEXT PRIMARY KEY,
                camera_make TEXT,                 -- Camera manufacturer
                camera_model TEXT,                -- Camera model
                lens_model TEXT,                  -- Lens model
                focal_length TEXT,                -- Focal length
                aperture TEXT,                    -- F-stop
                shutter_speed TEXT,               -- Shutter speed
                iso INTEGER,                      -- ISO value
                date_taken TIMESTAMP,             -- Original date/time
                gps_latitude REAL,                -- GPS latitude
                gps_longitude REAL,               -- GPS longitude
                FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE
            )
        """)

        # Note: recycle_bin table removed - photos.original_path column used instead

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_photos_path
            ON photos(file_path)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_photos_filename
            ON photos(filename)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_photos_created
            ON photos(created_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_photo_albums_album
            ON photo_albums(album_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_photo_tags_tag
            ON photo_tags(tag_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_photos_deleted
            ON photos(deleted_at)
        """)

        conn.commit()
