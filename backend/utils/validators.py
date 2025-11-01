"""Path validation utilities to prevent security issues."""

from pathlib import Path
from typing import Union

from backend.config import config


class PathValidationError(Exception):
    """Raised when path validation fails."""
    pass


def validate_path_in_photos_dir(path: Union[str, Path]) -> Path:
    """
    Validate that a path is within the photos directory.

    Args:
        path: Path to validate (can be relative or absolute)

    Returns:
        Absolute, resolved path within photos directory

    Raises:
        PathValidationError: If path is outside photos directory or invalid
    """
    try:
        # Convert to Path and resolve to absolute path
        if isinstance(path, str):
            path = Path(path)

        # Handle relative paths by making them relative to PHOTOS_PATH
        if not path.is_absolute():
            full_path = (config.PHOTOS_PATH / path).resolve()
        else:
            full_path = path.resolve()

        # Ensure path is within PHOTOS_PATH
        photos_path = config.PHOTOS_PATH.resolve()

        if not str(full_path).startswith(str(photos_path)):
            raise PathValidationError(
                f"Path '{path}' is outside photos directory"
            )

        return full_path

    except (ValueError, OSError) as e:
        raise PathValidationError(f"Invalid path '{path}': {e}")


def validate_folder_name(name: str) -> str:
    """
    Validate folder name for dangerous characters.

    Args:
        name: Folder name to validate

    Returns:
        Validated folder name

    Raises:
        PathValidationError: If folder name contains invalid characters
    """
    if not name:
        raise PathValidationError("Folder name cannot be empty")

    # Reject path traversal attempts
    if ".." in name or "/" in name or "\\" in name:
        raise PathValidationError(
            "Folder name cannot contain '..' or path separators"
        )

    # Reject hidden files/folders
    if name.startswith("."):
        raise PathValidationError("Folder name cannot start with '.'")

    return name


def get_relative_path(absolute_path: Path) -> str:
    """
    Get path relative to PHOTOS_PATH.

    Args:
        absolute_path: Absolute path within photos directory

    Returns:
        Path relative to PHOTOS_PATH as string
    """
    return str(absolute_path.relative_to(config.PHOTOS_PATH))
