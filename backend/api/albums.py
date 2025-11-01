"""API endpoints for album operations."""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from backend.database import get_db
from backend.dependencies import auth
from backend.models.album import (
    Album, AlbumCreate, AlbumUpdate, AlbumWithPhotos, AddPhotosRequest
)


router = APIRouter(prefix="/api/albums", tags=["albums"])


@router.get("", response_model=List[Album])
async def list_albums(authenticated: bool = Depends(auth)) -> List[Album]:
    """
    List all albums with photo counts.

    Returns:
        List of albums
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                a.id,
                a.name,
                a.description,
                a.created_at,
                COUNT(pa.photo_id) as photo_count
            FROM albums a
            LEFT JOIN photo_albums pa ON a.id = pa.album_id
            GROUP BY a.id
            ORDER BY a.name COLLATE NOCASE
        """)

        albums = [Album(**dict(row)) for row in cursor.fetchall()]

    return albums


@router.get("/{album_id}", response_model=AlbumWithPhotos)
async def get_album(album_id: str, authenticated: bool = Depends(auth)) -> AlbumWithPhotos:
    """
    Get album details with list of photo IDs.

    Args:
        album_id: Album ID

    Returns:
        Album with photo IDs
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get album
        cursor.execute("SELECT * FROM albums WHERE id = ?", (album_id,))
        album_row = cursor.fetchone()

        if not album_row:
            raise HTTPException(status_code=404, detail="Album not found")

        album_data = dict(album_row)

        # Get photo IDs
        cursor.execute(
            "SELECT photo_id FROM photo_albums WHERE album_id = ?",
            (album_id,)
        )
        photo_ids = [row["photo_id"] for row in cursor.fetchall()]

    return AlbumWithPhotos(**album_data, photo_ids=photo_ids)


@router.get("/{album_id}/photos")
async def get_album_photos(album_id: str, authenticated: bool = Depends(auth)):
    """
    Get all photos in an album with full photo details.

    Args:
        album_id: Album ID

    Returns:
        List of full photo objects
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Verify album exists
        cursor.execute("SELECT id FROM albums WHERE id = ?", (album_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Album not found")

        # Get all photos in this album with full details (exclude deleted)
        cursor.execute("""
            SELECT p.*
            FROM photos p
            INNER JOIN photo_albums pa ON p.id = pa.photo_id
            WHERE pa.album_id = ?
            AND p.deleted_at IS NULL
            ORDER BY p.filename COLLATE NOCASE
        """, (album_id,))

        photos = [dict(row) for row in cursor.fetchall()]

    return {"photos": photos}


@router.post("", response_model=Album)
async def create_album(request: AlbumCreate, authenticated: bool = Depends(auth)) -> Album:
    """
    Create a new album.

    Args:
        request: Album creation request

    Returns:
        Created album
    """
    album_id = str(uuid.uuid4())

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO albums (id, name, description)
                VALUES (?, ?, ?)
            """, (album_id, request.name, request.description))

            conn.commit()

            # Fetch created album
            cursor.execute("SELECT * FROM albums WHERE id = ?", (album_id,))
            album_row = cursor.fetchone()

        return Album(**dict(album_row), photo_count=0)

    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Album name already exists")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{album_id}", response_model=Album)
async def update_album(album_id: str, request: AlbumUpdate, authenticated: bool = Depends(auth)) -> Album:
    """
    Update album details.

    Args:
        album_id: Album ID
        request: Album update request

    Returns:
        Updated album
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if album exists
        cursor.execute("SELECT id FROM albums WHERE id = ?", (album_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Album not found")

        # Build update query
        updates = []
        params = []

        if request.name is not None:
            updates.append("name = ?")
            params.append(request.name)

        if request.description is not None:
            updates.append("description = ?")
            params.append(request.description)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(album_id)

        try:
            cursor.execute(
                f"UPDATE albums SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

            # Fetch updated album
            cursor.execute("""
                SELECT
                    a.id,
                    a.name,
                    a.description,
                    a.created_at,
                    COUNT(pa.photo_id) as photo_count
                FROM albums a
                LEFT JOIN photo_albums pa ON a.id = pa.album_id
                WHERE a.id = ?
                GROUP BY a.id
            """, (album_id,))

            album_row = cursor.fetchone()

            return Album(**dict(album_row))

        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(status_code=400, detail="Album name already exists")
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{album_id}")
async def delete_album(album_id: str, authenticated: bool = Depends(auth)):
    """
    Delete an album.

    Args:
        album_id: Album ID

    Returns:
        Deletion confirmation
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM albums WHERE id = ?", (album_id,))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Album not found")

        conn.commit()

    return {"message": "Album deleted successfully", "id": album_id}


@router.post("/{album_id}/photos")
async def add_photos_to_album(album_id: str, request: AddPhotosRequest, authenticated: bool = Depends(auth)):
    """
    Add photos to an album.

    Args:
        album_id: Album ID
        request: List of photo IDs to add

    Returns:
        Number of photos added
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if album exists
        cursor.execute("SELECT id FROM albums WHERE id = ?", (album_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Album not found")

        # Add photos (ignore duplicates)
        added = 0
        for photo_id in request.photo_ids:
            try:
                cursor.execute("""
                    INSERT INTO photo_albums (photo_id, album_id)
                    VALUES (?, ?)
                """, (photo_id, album_id))
                added += 1
            except Exception:
                # Ignore duplicates
                pass

        conn.commit()

    return {"message": f"Added {added} photos to album", "count": added}


@router.delete("/{album_id}/photos/{photo_id}")
async def remove_photo_from_album(album_id: str, photo_id: str, authenticated: bool = Depends(auth)):
    """
    Remove a photo from an album.

    Args:
        album_id: Album ID
        photo_id: Photo ID

    Returns:
        Removal confirmation
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM photo_albums
            WHERE album_id = ? AND photo_id = ?
        """, (album_id, photo_id))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Photo not in album")

        conn.commit()

    return {"message": "Photo removed from album"}
