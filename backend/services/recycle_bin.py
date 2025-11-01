"""Recycle bin service for soft-deleting and restoring photos."""

from typing import Dict, List

from backend.config import config
from backend.database import get_db


class RecycleBinError(Exception):
    """Raised when recycle bin operation fails."""
    pass


def delete_photo(photo_id: str) -> Dict:
    """
    Soft-delete a photo by setting deleted_at timestamp.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Dictionary with deletion info

    Raises:
        RecycleBinError: If deletion fails
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get photo info
        cursor.execute("SELECT filename FROM photos WHERE id = ? AND deleted_at IS NULL", (photo_id,))
        photo_row = cursor.fetchone()

        if not photo_row:
            raise RecycleBinError(f"Photo not found: {photo_id}")

        filename = photo_row["filename"]

        # Soft-delete by setting deleted_at timestamp
        cursor.execute(
            "UPDATE photos SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
            (photo_id,)
        )

        conn.commit()

        return {
            "id": photo_id,
            "filename": filename
        }


def restore_photo(photo_id: str) -> Dict:
    """
    Restore a photo from the recycle bin.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Dictionary with restoration info

    Raises:
        RecycleBinError: If restoration fails
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get photo from photos table
        cursor.execute(
            "SELECT filename FROM photos WHERE id = ? AND deleted_at IS NOT NULL",
            (photo_id,)
        )
        photo_row = cursor.fetchone()

        if not photo_row:
            raise RecycleBinError(f"Photo not found in recycle bin: {photo_id}")

        filename = photo_row["filename"]

        # Restore by clearing deleted_at timestamp
        cursor.execute(
            "UPDATE photos SET deleted_at = NULL WHERE id = ?",
            (photo_id,)
        )

        conn.commit()

        return {
            "id": photo_id,
            "filename": filename
        }


def list_recycle_bin() -> List[Dict]:
    """
    List all photos in the recycle bin.

    Returns:
        List of dictionaries with photo info
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, filename, file_path, file_size, deleted_at
            FROM photos
            WHERE deleted_at IS NOT NULL
            ORDER BY deleted_at DESC
        """)

        photos = []
        for row in cursor.fetchall():
            photos.append({
                "id": row["id"],
                "filename": row["filename"],
                "file_path": row["file_path"],
                "deleted_at": row["deleted_at"],
                "file_size": row["file_size"],
                "thumbnail_url": f"/api/photos/{row['id']}/thumbnail"
            })

        return photos


def permanent_delete(photo_id: str) -> Dict:
    """
    Permanently delete a photo from the recycle bin.
    
    Deletes both the database record and physical files (photo + thumbnail).

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Dictionary with deletion info

    Raises:
        RecycleBinError: If deletion fails
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get photo from photos table
        cursor.execute(
            "SELECT filename, file_path, thumbnail_path FROM photos WHERE id = ? AND deleted_at IS NOT NULL",
            (photo_id,)
        )
        photo_row = cursor.fetchone()

        if not photo_row:
            raise RecycleBinError(f"Photo not found in recycle bin: {photo_id}")

        filename = photo_row["filename"]
        file_path = photo_row["file_path"]
        thumbnail_path = photo_row["thumbnail_path"]

        # Delete physical photo file
        try:
            photo_file = config.PHOTOS_PATH / file_path
            if photo_file.exists():
                photo_file.unlink()
        except Exception as e:
            raise RecycleBinError(f"Failed to delete photo file: {e}")

        # Delete thumbnail if it exists
        try:
            if thumbnail_path:
                thumb_file = config.THUMBNAIL_PATH / thumbnail_path
                if thumb_file.exists():
                    thumb_file.unlink()
        except Exception:
            # Non-critical if thumbnail deletion fails
            pass

        # Delete from database (CASCADE will handle metadata, albums, tags)
        cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))

        conn.commit()

        return {
            "id": photo_id,
            "filename": filename
        }


def empty_recycle_bin() -> int:
    """
    Empty the entire recycle bin.
    
    Permanently deletes all soft-deleted photos including physical files.

    Returns:
        Number of photos permanently deleted

    Raises:
        RecycleBinError: If operation fails
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get all photos in recycle bin with their file paths
        cursor.execute("""
            SELECT id, file_path, thumbnail_path, filename 
            FROM photos 
            WHERE deleted_at IS NOT NULL
        """)
        photos = cursor.fetchall()

        count = 0
        errors = []
        
        for photo in photos:
            photo_id = photo["id"]
            file_path = photo["file_path"]
            thumbnail_path = photo["thumbnail_path"]
            
            try:
                # Delete physical photo file
                photo_file = config.PHOTOS_PATH / file_path
                if photo_file.exists():
                    photo_file.unlink()

                # Delete thumbnail if it exists
                if thumbnail_path:
                    thumb_file = config.THUMBNAIL_PATH / thumbnail_path
                    if thumb_file.exists():
                        thumb_file.unlink()

                count += 1
            except Exception as e:
                errors.append(f"Failed to delete files for {photo_id}: {str(e)}")

        # Delete all from database (CASCADE will handle metadata, albums, tags)
        cursor.execute("DELETE FROM photos WHERE deleted_at IS NOT NULL")
        
        conn.commit()

        # If there were file deletion errors, log them but still return success
        if errors:
            for error in errors[:5]:  # Only log first 5 errors
                print(f"Warning: {error}")

        return count
