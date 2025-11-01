"""API endpoints for photo operations."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

from backend.config import config
from backend.database import get_db
from backend.dependencies import auth
from backend.models.photo import (
    Photo, PhotoList, PhotoMetadata, MovePhotoRequest, RenamePhotoRequest
)
from backend.services.file_ops import move_photo, rename_photo, FileOperationError
from backend.services.recycle_bin import delete_photo, RecycleBinError
from backend.services.scanner import find_duplicates, scan_library
from backend.services.thumbnail import get_thumbnail_path, get_preview_path, generate_preview


router = APIRouter(prefix="/api/photos", tags=["photos"])


@router.get("", response_model=PhotoList)
async def list_photos(
    page: int = 1,
    limit: int = 50,
    authenticated: bool = Depends(auth)
) -> PhotoList:
    """
    List all photos with pagination.

    Args:
        page: Page number (1-indexed)
        limit: Photos per page

    Returns:
        Paginated list of photos
    """
    limit = min(limit, config.MAX_PAGE_SIZE)
    offset = (page - 1) * limit

    with get_db() as conn:
        cursor = conn.cursor()

        # Get total count (exclude deleted)
        cursor.execute("SELECT COUNT(*) as count FROM photos WHERE deleted_at IS NULL")
        total = cursor.fetchone()["count"]

        # Get paginated photos (exclude deleted)
        cursor.execute("""
            SELECT * FROM photos
            WHERE deleted_at IS NULL
            ORDER BY filename COLLATE NOCASE
            LIMIT ? OFFSET ?
        """, (limit, offset))

        photos = [dict(row) for row in cursor.fetchall()]

    total_pages = (total + limit - 1) // limit

    return PhotoList(
        photos=photos,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )


@router.get("/duplicates")
async def get_duplicates(authenticated: bool = Depends(auth)):
    """
    Find duplicate photos by scanning filesystem.

    Returns:
        List of duplicate groups
    """
    duplicates = find_duplicates()
    return {"duplicates": duplicates, "count": len(duplicates)}


@router.get("/{photo_id}", response_model=Photo)
async def get_photo(photo_id: str, authenticated: bool = Depends(auth)) -> Photo:
    """
    Get photo details with EXIF metadata.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Full photo details
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get photo (exclude deleted)
        cursor.execute("SELECT * FROM photos WHERE id = ? AND deleted_at IS NULL", (photo_id,))
        photo_row = cursor.fetchone()

        if not photo_row:
            raise HTTPException(status_code=404, detail="Photo not found")

        photo_data = dict(photo_row)

        # Get metadata
        cursor.execute("SELECT * FROM metadata WHERE photo_id = ?", (photo_id,))
        metadata_row = cursor.fetchone()

        metadata = None
        if metadata_row:
            metadata_dict = dict(metadata_row)
            metadata_dict.pop("photo_id", None)  # Remove photo_id field
            metadata = PhotoMetadata(**metadata_dict)

    return Photo(**photo_data, metadata=metadata)


@router.get("/{photo_id}/albums")
async def get_photo_albums(photo_id: str, authenticated: bool = Depends(auth)):
    """
    Get all albums containing this photo.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        List of albums containing this photo
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Verify photo exists (exclude deleted)
        cursor.execute("SELECT id FROM photos WHERE id = ? AND deleted_at IS NULL", (photo_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Photo not found")

        # Get albums for this photo
        cursor.execute("""
            SELECT a.id, a.name, a.description, a.created_at
            FROM albums a
            INNER JOIN photo_albums pa ON a.id = pa.album_id
            WHERE pa.photo_id = ?
            ORDER BY a.name COLLATE NOCASE
        """, (photo_id,))

        albums = []
        for row in cursor.fetchall():
            albums.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "created_at": row["created_at"]
            })

    return {"albums": albums}


@router.get("/{photo_id}/tags")
async def get_photo_tags(photo_id: str, authenticated: bool = Depends(auth)):
    """
    Get all tags for this photo.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        List of tags associated with this photo
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Verify photo exists (exclude deleted)
        cursor.execute("SELECT id FROM photos WHERE id = ? AND deleted_at IS NULL", (photo_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Photo not found")

        # Get tags for this photo
        cursor.execute("""
            SELECT t.id, t.name
            FROM tags t
            INNER JOIN photo_tags pt ON t.id = pt.tag_id
            WHERE pt.photo_id = ?
            ORDER BY t.name COLLATE NOCASE
        """, (photo_id,))

        tags = []
        for row in cursor.fetchall():
            tags.append({
                "id": row["id"],
                "name": row["name"]
            })

    return {"tags": tags}


@router.get("/{photo_id}/thumbnail")
async def get_thumbnail(photo_id: str, authenticated: bool = Depends(auth)):
    """
    Get thumbnail image for a photo.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Thumbnail image file
    """
    thumbnail_path = get_thumbnail_path(photo_id)

    if not thumbnail_path or not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(
        thumbnail_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000"}  # Cache for 1 year
    )


@router.get("/{photo_id}/preview")
async def get_preview(photo_id: str, authenticated: bool = Depends(auth)):
    """
    Get medium-size preview image for a photo (optimized for lightbox).

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Preview image file
    """
    preview_path = get_preview_path(photo_id)

    # Generate preview if it doesn't exist
    if not preview_path or not preview_path.exists():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM photos WHERE id = ? AND deleted_at IS NULL", (photo_id,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Photo not found")

            photo_path = config.PHOTOS_PATH / row["file_path"]
            if not photo_path.exists():
                raise HTTPException(status_code=404, detail="Photo file not found")

            preview_path = generate_preview(photo_path, photo_id)
            if not preview_path:
                raise HTTPException(status_code=500, detail="Failed to generate preview")

    return FileResponse(
        preview_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000"}  # Cache for 1 year
    )


@router.get("/{photo_id}/image")
async def get_full_image(photo_id: str, authenticated: bool = Depends(auth)):
    """
    Get full-size image for a photo.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Full-size image file
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, mime_type FROM photos WHERE id = ? AND deleted_at IS NULL", (photo_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Photo not found")

        photo_path = config.PHOTOS_PATH / row["file_path"]

        if not photo_path.exists():
            raise HTTPException(status_code=404, detail="Photo file not found")

        return FileResponse(
            photo_path,
            media_type=row["mime_type"] or "image/jpeg",
            headers={"Cache-Control": "public, max-age=31536000"}  # Cache for 1 year
        )


@router.put("/{photo_id}/move")
async def move_photo_endpoint(photo_id: str, request: MovePhotoRequest, authenticated: bool = Depends(auth)):
    """
    Move photo to a new folder.

    Args:
        photo_id: Photo ID (SHA256 hash)
        request: Move request with destination folder

    Returns:
        New file path
    """
    try:
        new_path = move_photo(photo_id, request.folder_path)
        return {"id": photo_id, "new_path": new_path}
    except FileOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{photo_id}/rename")
async def rename_photo_endpoint(photo_id: str, request: RenamePhotoRequest, authenticated: bool = Depends(auth)):
    """
    Rename a photo.

    Args:
        photo_id: Photo ID (SHA256 hash)
        request: Rename request with new filename

    Returns:
        New file path
    """
    try:
        new_path = rename_photo(photo_id, request.new_filename)
        return {"id": photo_id, "new_path": new_path, "filename": request.new_filename}
    except FileOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{photo_id}")
async def delete_photo_endpoint(photo_id: str, authenticated: bool = Depends(auth)):
    """
    Delete photo (soft delete to recycle bin).

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Deletion confirmation
    """
    try:
        result = delete_photo(photo_id)
        return {"message": "Photo moved to recycle bin", **result}
    except RecycleBinError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scan")
async def scan_photos(authenticated: bool = Depends(auth)):
    """
    Trigger a library scan to index new photos.

    Returns:
        Scan statistics
    """
    stats = scan_library()
    return {"message": "Scan complete", "stats": stats}
