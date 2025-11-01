"""API endpoints for recycle bin operations."""

from fastapi import APIRouter, HTTPException, Depends

from backend.dependencies import auth
from backend.services.recycle_bin import (
    list_recycle_bin, restore_photo, permanent_delete, empty_recycle_bin, RecycleBinError
)


router = APIRouter(prefix="/api/recycle-bin", tags=["recycle-bin"])


@router.get("")
async def list_deleted_photos(authenticated: bool = Depends(auth)):
    """
    List all photos in the recycle bin.

    Returns:
        List of deleted photos
    """
    photos = list_recycle_bin()
    return {"photos": photos, "count": len(photos)}


@router.delete("/empty")
async def empty_recycle_bin_endpoint(authenticated: bool = Depends(auth)):
    """
    Empty the entire recycle bin.

    Returns:
        Number of photos deleted
    """
    print("DEBUG: Empty recycle bin endpoint called")
    try:
        count = empty_recycle_bin()
        print(f"DEBUG: Successfully deleted {count} photos")
        return {"message": f"Recycle bin emptied ({count} photos deleted)", "count": count}
    except RecycleBinError as e:
        print(f"DEBUG: RecycleBinError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{photo_id}/restore")
async def restore_photo_endpoint(photo_id: str, authenticated: bool = Depends(auth)):
    """
    Restore a photo from the recycle bin.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Restoration confirmation
    """
    try:
        result = restore_photo(photo_id)
        return {"message": "Photo restored successfully", **result}
    except RecycleBinError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{photo_id}")
async def permanent_delete_endpoint(photo_id: str, authenticated: bool = Depends(auth)):
    """
    Permanently delete a photo from the recycle bin.

    Args:
        photo_id: Photo ID (SHA256 hash)

    Returns:
        Deletion confirmation
    """
    try:
        result = permanent_delete(photo_id)
        return {"message": "Photo permanently deleted", **result}
    except RecycleBinError as e:
        raise HTTPException(status_code=400, detail=str(e))
