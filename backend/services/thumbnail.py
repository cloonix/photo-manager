"""Thumbnail generation service for photos."""

from pathlib import Path
from typing import Optional

from PIL import Image

from backend.config import config


def generate_thumbnail(file_path: Path, photo_id: str) -> Optional[Path]:
    """
    Generate thumbnail for a photo.

    Args:
        file_path: Path to original photo
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Path to generated thumbnail or None if generation failed
    """
    thumbnail_path = config.THUMBNAIL_PATH / f"{photo_id}.jpg"

    # Skip if thumbnail already exists (content-based ID means it never changes)
    if thumbnail_path.exists():
        return thumbnail_path

    try:
        # Check if this is a RAW file
        ext = file_path.suffix.lower()
        if ext in {".cr2", ".cr3", ".nef", ".arf", ".dng", ".orf", ".rw2", ".arw"}:
            return _generate_raw_thumbnail(file_path, thumbnail_path)
        else:
            return _generate_standard_thumbnail(file_path, thumbnail_path)

    except Exception as e:
        print(f"Error generating thumbnail for {file_path}: {e}")
        return None


def generate_preview(file_path: Path, photo_id: str, size: int = 1200) -> Optional[Path]:
    """
    Generate medium-size preview for a photo (for lightbox display).

    Args:
        file_path: Path to original photo
        photo_id: Photo ID (SHA256 hash)
        size: Max dimension for preview (default 1200px)

    Returns:
        Path to generated preview or None if generation failed
    """
    preview_path = config.THUMBNAIL_PATH / f"{photo_id}_preview.jpg"

    # Skip if preview already exists
    if preview_path.exists():
        return preview_path

    try:
        # Check if this is a RAW file
        ext = file_path.suffix.lower()
        if ext in {".cr2", ".cr3", ".nef", ".arf", ".dng", ".orf", ".rw2", ".arw"}:
            return _generate_raw_preview(file_path, preview_path, size)
        else:
            return _generate_standard_preview(file_path, preview_path, size)

    except Exception as e:
        print(f"Error generating preview for {file_path}: {e}")
        return None


def _generate_standard_preview(file_path: Path, preview_path: Path, size: int) -> Path:
    """Generate medium-size preview for standard image formats."""
    with Image.open(file_path) as img:
        # Convert to RGB if needed
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Only resize if image is larger than target size
        if max(img.size) > size:
            img.thumbnail((size, size), Image.Resampling.LANCZOS)

        # Save as JPEG with good quality
        img.save(preview_path, "JPEG", quality=90, optimize=True)

    return preview_path


def _generate_raw_preview(file_path: Path, preview_path: Path, size: int) -> Path:
    """Generate medium-size preview for RAW image formats."""
    try:
        import rawpy
    except ImportError:
        print("rawpy not available, cannot process RAW files")
        raise

    with rawpy.imread(str(file_path)) as raw:
        # Render RAW to RGB array
        rgb = raw.postprocess(
            use_camera_wb=True,
            half_size=False,  # Full quality for preview
            no_auto_bright=False,
            output_bps=8
        )

        # Convert to PIL Image and resize if needed
        img = Image.fromarray(rgb)
        if max(img.size) > size:
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
        
        img.save(preview_path, "JPEG", quality=90, optimize=True)

    return preview_path


def get_preview_path(photo_id: str) -> Optional[Path]:
    """
    Get path to preview if it exists.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Path to preview or None if it doesn't exist
    """
    preview_path = config.THUMBNAIL_PATH / f"{photo_id}_preview.jpg"
    return preview_path if preview_path.exists() else None


def _generate_standard_thumbnail(file_path: Path, thumbnail_path: Path) -> Path:
    """
    Generate thumbnail for standard image formats (JPEG, PNG, GIF, WebP).

    Args:
        file_path: Path to original photo
        thumbnail_path: Path where thumbnail should be saved

    Returns:
        Path to generated thumbnail
    """
    with Image.open(file_path) as img:
        # Convert to RGB if needed (handles RGBA, grayscale, etc.)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Calculate thumbnail size (max dimension = THUMBNAIL_SIZE)
        img.thumbnail(
            (config.THUMBNAIL_SIZE, config.THUMBNAIL_SIZE),
            Image.Resampling.LANCZOS
        )

        # Save as JPEG
        img.save(
            thumbnail_path,
            "JPEG",
            quality=config.THUMBNAIL_QUALITY,
            optimize=True
        )

    return thumbnail_path


def _generate_raw_thumbnail(file_path: Path, thumbnail_path: Path) -> Path:
    """
    Generate thumbnail for RAW image formats.

    Args:
        file_path: Path to original RAW photo
        thumbnail_path: Path where thumbnail should be saved

    Returns:
        Path to generated thumbnail
    """
    try:
        import rawpy
    except ImportError:
        print("rawpy not available, cannot process RAW files")
        raise

    with rawpy.imread(str(file_path)) as raw:
        # Try to extract embedded JPEG preview first (faster)
        try:
            thumb = raw.extract_thumb()
            if thumb.format == rawpy.ThumbFormat.JPEG:
                # Save embedded JPEG thumbnail
                with open(thumbnail_path, 'wb') as f:
                    f.write(thumb.data)

                # Resize if needed
                with Image.open(thumbnail_path) as img:
                    if max(img.size) > config.THUMBNAIL_SIZE:
                        img.thumbnail(
                            (config.THUMBNAIL_SIZE, config.THUMBNAIL_SIZE),
                            Image.Resampling.LANCZOS
                        )
                        img.save(
                            thumbnail_path,
                            "JPEG",
                            quality=config.THUMBNAIL_QUALITY,
                            optimize=True
                        )
                return thumbnail_path

        except (rawpy.LibRawError, Exception):
            # If preview extraction fails, render the RAW file
            pass

        # Render RAW to RGB array (slower but works for all RAW formats)
        rgb = raw.postprocess(
            use_camera_wb=True,
            half_size=True,  # Speed optimization
            no_auto_bright=False,
            output_bps=8
        )

        # Convert to PIL Image and create thumbnail
        img = Image.fromarray(rgb)
        img.thumbnail(
            (config.THUMBNAIL_SIZE, config.THUMBNAIL_SIZE),
            Image.Resampling.LANCZOS
        )
        img.save(
            thumbnail_path,
            "JPEG",
            quality=config.THUMBNAIL_QUALITY,
            optimize=True
        )

    return thumbnail_path


def get_thumbnail_path(photo_id: str) -> Optional[Path]:
    """
    Get path to thumbnail if it exists.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Path to thumbnail or None if it doesn't exist
    """
    thumbnail_path = config.THUMBNAIL_PATH / f"{photo_id}.jpg"
    return thumbnail_path if thumbnail_path.exists() else None
