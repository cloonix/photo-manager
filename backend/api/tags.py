"""API endpoints for tag operations."""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from backend.database import get_db
from backend.dependencies import auth
from backend.models.tag import Tag, TagCreate, TagUpdate, AddPhotosRequest


router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=List[Tag])
async def list_tags(authenticated: bool = Depends(auth)) -> List[Tag]:
    """
    List all tags with photo counts.

    Returns:
        List of tags
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                t.id,
                t.name,
                COUNT(pt.photo_id) as photo_count
            FROM tags t
            LEFT JOIN photo_tags pt ON t.id = pt.tag_id
            GROUP BY t.id
            ORDER BY t.name COLLATE NOCASE
        """)

        tags = [Tag(**dict(row)) for row in cursor.fetchall()]

    return tags


@router.post("", response_model=Tag)
async def create_tag(request: TagCreate, authenticated: bool = Depends(auth)) -> Tag:
    """
    Create a new tag.

    Args:
        request: Tag creation request

    Returns:
        Created tag
    """
    tag_id = str(uuid.uuid4())

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO tags (id, name)
                VALUES (?, ?)
            """, (tag_id, request.name))

            conn.commit()

        return Tag(id=tag_id, name=request.name, photo_count=0)

    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Tag name already exists")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tag_id}", response_model=Tag)
async def update_tag(tag_id: str, request: TagUpdate, authenticated: bool = Depends(auth)) -> Tag:
    """
    Update tag name.

    Args:
        tag_id: Tag ID
        request: Tag update request

    Returns:
        Updated tag
    """
    with get_db() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE tags SET name = ? WHERE id = ?",
                (request.name, tag_id)
            )

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Tag not found")

            conn.commit()

            # Fetch updated tag with photo count
            cursor.execute("""
                SELECT
                    t.id,
                    t.name,
                    COUNT(pt.photo_id) as photo_count
                FROM tags t
                LEFT JOIN photo_tags pt ON t.id = pt.tag_id
                WHERE t.id = ?
                GROUP BY t.id
            """, (tag_id,))

            tag_row = cursor.fetchone()

            return Tag(**dict(tag_row))

        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(status_code=400, detail="Tag name already exists")
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str, authenticated: bool = Depends(auth)):
    """
    Delete a tag.

    Args:
        tag_id: Tag ID

    Returns:
        Deletion confirmation
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tag not found")

        conn.commit()

    return {"message": "Tag deleted successfully", "id": tag_id}


@router.post("/{tag_id}/photos")
async def add_photos_to_tag(tag_id: str, request: AddPhotosRequest, authenticated: bool = Depends(auth)):
    """
    Tag photos with this tag.

    Args:
        tag_id: Tag ID
        request: List of photo IDs to tag

    Returns:
        Number of photos tagged
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if tag exists
        cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Tag not found")

        # Tag photos (ignore duplicates)
        added = 0
        for photo_id in request.photo_ids:
            try:
                cursor.execute("""
                    INSERT INTO photo_tags (photo_id, tag_id)
                    VALUES (?, ?)
                """, (photo_id, tag_id))
                added += 1
            except Exception:
                # Ignore duplicates
                pass

        conn.commit()

    return {"message": f"Tagged {added} photos", "count": added}


@router.delete("/{tag_id}/photos/{photo_id}")
async def remove_tag_from_photo(tag_id: str, photo_id: str, authenticated: bool = Depends(auth)):
    """
    Remove a tag from a photo.

    Args:
        tag_id: Tag ID
        photo_id: Photo ID

    Returns:
        Removal confirmation
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM photo_tags
            WHERE tag_id = ? AND photo_id = ?
        """, (tag_id, photo_id))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Photo not tagged with this tag")

        conn.commit()

    return {"message": "Tag removed from photo"}
