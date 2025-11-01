"""Photo library scanner service."""

import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PIL import Image

from backend.config import config
from backend.database import get_db
from backend.services.exif import extract_exif_data
from backend.services.thumbnail import generate_thumbnail
from backend.utils.hashing import compute_file_hash
from backend.utils.validators import get_relative_path


def scan_library() -> Dict[str, int]:
    """
    Scan the photos directory and index all photos.

    Returns:
        Dictionary with scan statistics
    """
    stats = {
        "scanned": 0,
        "indexed": 0,
        "skipped": 0,
        "errors": 0
    }

    print(f"Starting library scan of {config.PHOTOS_PATH}")

    for file_path in _walk_photos_directory():
        stats["scanned"] += 1

        try:
            if index_photo(file_path):
                stats["indexed"] += 1
            else:
                stats["skipped"] += 1

            # Log progress every 100 photos
            if stats["scanned"] % 100 == 0:
                print(f"Scanned {stats['scanned']} photos...")

        except Exception as e:
            stats["errors"] += 1
            print(f"Error indexing {file_path}: {e}")

    print(f"Scan complete: {stats}")
    return stats


def _walk_photos_directory() -> List[Path]:
    """
    Recursively walk photos directory and find all image files.

    Returns:
        List of paths to photo files
    """
    photo_files = []

    for file_path in config.PHOTOS_PATH.rglob("*"):
        if not file_path.is_file():
            continue

        # Check if file extension is supported
        if file_path.suffix.lower() in config.SUPPORTED_FORMATS:
            photo_files.append(file_path)

    return photo_files


def index_photo(file_path: Path) -> bool:
    """
    Index a single photo file.

    Args:
        file_path: Path to photo file

    Returns:
        True if photo was indexed, False if skipped (duplicate)
    """
    # Compute hash
    photo_id = compute_file_hash(file_path)
    relative_path = get_relative_path(file_path)

    # Check if photo already exists
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, deleted_at FROM photos WHERE id = ?", (photo_id,))
        existing = cursor.fetchone()
        if existing:
            # If photo was soft-deleted, restore it
            if existing["deleted_at"]:
                cursor.execute(
                    "UPDATE photos SET deleted_at = NULL, file_path = ?, indexed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (relative_path, photo_id)
                )
                conn.commit()
                return True
            # Photo already indexed (duplicate)
            return False

        # Get file info
        stat = file_path.stat()
        relative_path = get_relative_path(file_path)
        filename = file_path.name

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))

        # Get image dimensions
        width, height = _get_image_dimensions(file_path)

        # Get file timestamps
        created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
        modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

        # Insert photo record
        cursor.execute("""
            INSERT INTO photos (
                id, file_path, filename, file_size, mime_type,
                width, height, created_at, modified_at, indexed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            photo_id,
            relative_path,
            filename,
            stat.st_size,
            mime_type,
            width,
            height,
            created_at,
            modified_at,
            datetime.now().isoformat()
        ))

        # Extract and store EXIF metadata
        metadata = extract_exif_data(file_path)

        # Use EXIF date if available
        if metadata.get("date_taken"):
            cursor.execute(
                "UPDATE photos SET created_at = ? WHERE id = ?",
                (metadata["date_taken"], photo_id)
            )

        # Insert metadata
        cursor.execute("""
            INSERT INTO metadata (
                photo_id, camera_make, camera_model, lens_model,
                focal_length, aperture, shutter_speed, iso,
                date_taken, gps_latitude, gps_longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            photo_id,
            metadata.get("camera_make"),
            metadata.get("camera_model"),
            metadata.get("lens_model"),
            metadata.get("focal_length"),
            metadata.get("aperture"),
            metadata.get("shutter_speed"),
            metadata.get("iso"),
            metadata.get("date_taken"),
            metadata.get("gps_latitude"),
            metadata.get("gps_longitude")
        ))

        conn.commit()

    # Generate thumbnail (async in background would be better, but keep it simple for MVP)
    try:
        thumbnail_path = generate_thumbnail(file_path, photo_id)
        if thumbnail_path:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE photos SET thumbnail_path = ? WHERE id = ?",
                    (str(thumbnail_path), photo_id)
                )
    except Exception as e:
        print(f"Warning: Failed to generate thumbnail for {file_path}: {e}")

    return True


def _get_image_dimensions(file_path: Path) -> tuple[int, int]:
    """
    Get image dimensions.

    Args:
        file_path: Path to image file

    Returns:
        Tuple of (width, height)
    """
    try:
        # For RAW files, try to get dimensions from EXIF
        if file_path.suffix.lower() in {".cr2", ".cr3", ".nef", ".arf", ".dng", ".orf", ".rw2", ".arw"}:
            try:
                import rawpy
                with rawpy.imread(str(file_path)) as raw:
                    return raw.sizes.width, raw.sizes.height
            except Exception:
                pass

        # For standard formats, use PIL
        with Image.open(file_path) as img:
            return img.size

    except Exception as e:
        print(f"Warning: Could not get dimensions for {file_path}: {e}")
        return 0, 0


def find_duplicates() -> List[Dict]:
    """
    Find duplicate photos by scanning filesystem and comparing hashes.

    Returns:
        List of duplicate groups with photo info
    """
    duplicates = []
    hash_map = {}

    # Build map of hashes from database (exclude deleted)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, file_path FROM photos WHERE deleted_at IS NULL")
        for row in cursor.fetchall():
            hash_map[row["id"]] = {
                "photo_id": row["id"],
                "indexed_path": row["file_path"],
                "duplicates": []
            }

    # Scan filesystem for files with same hashes
    for file_path in _walk_photos_directory():
        try:
            photo_hash = compute_file_hash(file_path)
            relative_path = get_relative_path(file_path)

            # If hash exists in database and path is different
            if photo_hash in hash_map:
                if relative_path != hash_map[photo_hash]["indexed_path"]:
                    hash_map[photo_hash]["duplicates"].append(relative_path)

        except Exception as e:
            print(f"Error checking {file_path}: {e}")

    # Filter to only groups with duplicates
    for photo_id, data in hash_map.items():
        if data["duplicates"]:
            duplicates.append(data)

    return duplicates
