"""API endpoints for folder operations."""

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.config import config
from backend.database import get_db
from backend.dependencies import auth
from backend.services.file_ops import create_folder, FileOperationError
from backend.utils.validators import get_relative_path


router = APIRouter(prefix="/api/folders", tags=["folders"])


class FolderNode(BaseModel):
    """Folder tree node."""
    name: str
    path: str
    photo_count: int
    children: List['FolderNode'] = []


class FolderCreate(BaseModel):
    """Request to create a folder."""
    path: str


class PhotoInFolder(BaseModel):
    """Photo in a folder."""
    id: str
    filename: str
    thumbnail_url: str


@router.get("")
async def get_folder_tree(authenticated: bool = Depends(auth)) -> Dict:
    """
    Get hierarchical folder tree with recursive photo counts.

    Returns:
        Root folder node with nested children
    """
    root = _build_folder_tree(config.PHOTOS_PATH)
    return root


@router.get("/{path:path}")
async def get_folder_photos(
    path: str = "",
    page: int = 1,
    limit: int = 50,
    authenticated: bool = Depends(auth)
) -> Dict:
    """
    List photos in a specific folder (non-recursive).

    Args:
        path: Relative folder path
        page: Page number (1-indexed)
        limit: Photos per page

    Returns:
        Paginated list of photos in folder
    """
    # Build folder path
    if path:
        folder_path = config.PHOTOS_PATH / path
    else:
        folder_path = config.PHOTOS_PATH

    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    # Get photos in this folder only (not subdirectories)
    with get_db() as conn:
        cursor = conn.cursor()

        if path:
            # For a specific folder, match files that start with "folder/" and have no additional "/"
            # Example: "Wallpaper/file.jpg" matches, but "Wallpaper/Cats/file.jpg" doesn't
            folder_prefix = f"{path}/"
            
            # Get total count (exclude deleted)
            cursor.execute("""
                SELECT COUNT(*) as count FROM photos
                WHERE file_path LIKE ? 
                AND (LENGTH(file_path) - LENGTH(REPLACE(file_path, '/', ''))) = ?
                AND deleted_at IS NULL
            """, (f"{folder_prefix}%", path.count('/') + 1))
            
            total = cursor.fetchone()["count"]

            # Get paginated photos (exclude deleted)
            offset = (page - 1) * limit

            cursor.execute("""
                SELECT id, filename, file_path
                FROM photos
                WHERE file_path LIKE ? 
                AND (LENGTH(file_path) - LENGTH(REPLACE(file_path, '/', ''))) = ?
                AND deleted_at IS NULL
                ORDER BY filename COLLATE NOCASE
                LIMIT ? OFFSET ?
            """, (f"{folder_prefix}%", path.count('/') + 1, limit, offset))
        else:
            # For root folder, match files with no "/" in path (exclude deleted)
            cursor.execute("""
                SELECT COUNT(*) as count FROM photos
                WHERE file_path NOT LIKE '%/%'
                AND deleted_at IS NULL
            """)
            
            total = cursor.fetchone()["count"]

            # Get paginated photos (exclude deleted)
            offset = (page - 1) * limit

            cursor.execute("""
                SELECT id, filename, file_path
                FROM photos
                WHERE file_path NOT LIKE '%/%'
                AND deleted_at IS NULL
                ORDER BY filename COLLATE NOCASE
                LIMIT ? OFFSET ?
            """, (limit, offset))

        photos = []
        for row in cursor.fetchall():
            photos.append({
                "id": row["id"],
                "filename": row["filename"],
                "thumbnail_url": f"/api/photos/{row['id']}/thumbnail"
            })

    total_pages = (total + limit - 1) // limit

    return {
        "photos": photos,
        "total": total,
        "page": page,
        "page_size": limit,
        "total_pages": total_pages
    }


@router.post("")
async def create_new_folder(request: FolderCreate, authenticated: bool = Depends(auth)) -> Dict:
    """
    Create a new folder.

    Args:
        request: Folder creation request

    Returns:
        Created folder info
    """
    try:
        relative_path = create_folder(request.path)
        return {
            "path": relative_path,
            "message": "Folder created successfully"
        }
    except FileOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{path:path}")
async def delete_folder(path: str, authenticated: bool = Depends(auth)) -> Dict:
    """
    Delete an empty folder.

    Args:
        path: Relative folder path

    Returns:
        Success message
    """
    if not path:
        raise HTTPException(status_code=400, detail="Cannot delete root folder")

    # Build absolute path
    folder_path = config.PHOTOS_PATH / path

    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")

    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a folder")

    # Check if folder is empty (no files or subfolders)
    try:
        contents = list(folder_path.iterdir())
        if contents:
            raise HTTPException(
                status_code=400,
                detail=f"Folder is not empty. Contains {len(contents)} items."
            )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Delete the empty folder
    try:
        folder_path.rmdir()
        return {
            "path": path,
            "message": "Folder deleted successfully"
        }
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")


def _build_folder_tree(folder_path: Path, root_path: Optional[Path] = None) -> Dict:
    """
    Recursively build folder tree with photo counts.

    Args:
        folder_path: Current folder path
        root_path: Root path for calculating relative paths

    Returns:
        Folder node dictionary
    """
    if root_path is None:
        root_path = config.PHOTOS_PATH

    # Get relative path for display
    if folder_path == root_path:
        name = "Photos"
        relative_path = ""
    else:
        name = folder_path.name
        relative_path = get_relative_path(folder_path)

    # Get recursive photo count (exclude deleted)
    with get_db() as conn:
        cursor = conn.cursor()

        if relative_path:
            # Count photos in this folder and all subfolders (exclude deleted)
            cursor.execute("""
                SELECT COUNT(*) as count FROM photos
                WHERE file_path LIKE ?
                AND deleted_at IS NULL
            """, (f"{relative_path}%",))
        else:
            # Root folder - count all photos (exclude deleted)
            cursor.execute("SELECT COUNT(*) as count FROM photos WHERE deleted_at IS NULL")

        photo_count = cursor.fetchone()["count"]

    # Get immediate subfolders
    children = []
    try:
        for child_path in sorted(folder_path.iterdir()):
            # Exclude hidden folders (including .recycle-bin which has its own sidebar item)
            if child_path.is_dir() and not child_path.name.startswith('.'):
                child_node = _build_folder_tree(child_path, root_path)
                children.append(child_node)
    except PermissionError:
        pass  # Skip folders we can't access

    return {
        "name": name,
        "path": relative_path,
        "photo_count": photo_count,
        "children": children
    }


# Allow recursive reference
FolderNode.model_rebuild()
