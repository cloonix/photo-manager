"""File operations service for moving, renaming, and deleting photos."""

import shutil
from pathlib import Path

from backend.config import config
from backend.database import get_db
from backend.utils.validators import validate_path_in_photos_dir, validate_folder_name, get_relative_path


class FileOperationError(Exception):
    """Raised when file operation fails."""
    pass


def move_photo(photo_id: str, new_folder_path: str) -> str:
    """
    Move a photo to a new folder.

    Args:
        photo_id: Photo ID (SHA256 hash)
        new_folder_path: Relative path to destination folder

    Returns:
        New relative file path

    Raises:
        FileOperationError: If move operation fails
    """
    # Validate destination path
    dest_folder = validate_path_in_photos_dir(new_folder_path)

    if not dest_folder.exists():
        raise FileOperationError(f"Destination folder does not exist: {new_folder_path}")

    if not dest_folder.is_dir():
        raise FileOperationError(f"Destination is not a folder: {new_folder_path}")

    # Get current photo info (exclude deleted)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, filename FROM photos WHERE id = ? AND deleted_at IS NULL", (photo_id,))
        row = cursor.fetchone()

        if not row:
            raise FileOperationError(f"Photo not found: {photo_id}")

        current_path = config.PHOTOS_PATH / row["file_path"]
        filename = row["filename"]

        # Build new path
        new_path = dest_folder / filename

        # Check if destination already exists
        if new_path.exists():
            raise FileOperationError(f"File already exists at destination: {filename}")

        # Move file
        try:
            shutil.move(str(current_path), str(new_path))
        except Exception as e:
            raise FileOperationError(f"Failed to move file: {e}")

        # Update database
        new_relative_path = get_relative_path(new_path)
        cursor.execute(
            "UPDATE photos SET file_path = ? WHERE id = ?",
            (new_relative_path, photo_id)
        )
        conn.commit()

        return new_relative_path


def rename_photo(photo_id: str, new_filename: str) -> str:
    """
    Rename a photo.

    Args:
        photo_id: Photo ID (SHA256 hash)
        new_filename: New filename (with extension)

    Returns:
        New relative file path

    Raises:
        FileOperationError: If rename operation fails
    """
    # Validate filename (basic check)
    if not new_filename or "/" in new_filename or "\\" in new_filename:
        raise FileOperationError("Invalid filename")

    # Get current photo info (exclude deleted)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM photos WHERE id = ? AND deleted_at IS NULL", (photo_id,))
        row = cursor.fetchone()

        if not row:
            raise FileOperationError(f"Photo not found: {photo_id}")

        current_path = config.PHOTOS_PATH / row["file_path"]
        parent_folder = current_path.parent

        # Build new path
        new_path = parent_folder / new_filename

        # Check if destination already exists
        if new_path.exists() and new_path != current_path:
            raise FileOperationError(f"File already exists: {new_filename}")

        # Rename file
        try:
            current_path.rename(new_path)
        except Exception as e:
            raise FileOperationError(f"Failed to rename file: {e}")

        # Update database
        new_relative_path = get_relative_path(new_path)
        cursor.execute(
            "UPDATE photos SET filename = ?, file_path = ? WHERE id = ?",
            (new_filename, new_relative_path, photo_id)
        )
        conn.commit()

        return new_relative_path


def create_folder(folder_path: str) -> str:
    """
    Create a new folder in the photos directory.

    Args:
        folder_path: Relative path for new folder

    Returns:
        Relative path to created folder

    Raises:
        FileOperationError: If folder creation fails
    """
    # Validate path
    full_path = validate_path_in_photos_dir(folder_path)

    # Check if folder already exists
    if full_path.exists():
        raise FileOperationError(f"Folder already exists: {folder_path}")

    # Ensure parent directory exists
    if not full_path.parent.exists():
        raise FileOperationError(f"Parent folder does not exist: {full_path.parent}")

    # Validate folder name
    folder_name = full_path.name
    validate_folder_name(folder_name)

    # Create folder
    try:
        full_path.mkdir(parents=False, exist_ok=False)
    except Exception as e:
        raise FileOperationError(f"Failed to create folder: {e}")

    return get_relative_path(full_path)
