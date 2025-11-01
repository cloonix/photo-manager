"""API endpoints for search operations."""

from typing import Optional

from fastapi import APIRouter, Depends

from backend.config import config
from backend.database import get_db
from backend.dependencies import auth
from backend.models.photo import PhotoList


router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=PhotoList)
async def search_photos(
    q: Optional[str] = None,
    tags: Optional[str] = None,
    albums: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    authenticated: bool = Depends(auth)
) -> PhotoList:
    """
    Search photos by filename, tags, albums, and date range.

    Args:
        q: Filename search query (partial match, case-insensitive)
        tags: Comma-separated tag names (AND logic)
        albums: Comma-separated album names (OR logic)
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        page: Page number (1-indexed)
        limit: Photos per page

    Returns:
        Paginated search results
    """
    limit = min(limit, config.MAX_PAGE_SIZE)
    offset = (page - 1) * limit

    # Build WHERE clauses
    where_clauses = []
    params = []

    # Exclude deleted photos
    where_clauses.append("p.deleted_at IS NULL")

    # Filename search
    if q:
        where_clauses.append("p.filename LIKE ?")
        params.append(f"%{q}%")

    # Date range filter
    if from_date:
        where_clauses.append("p.created_at >= ?")
        params.append(from_date)

    if to_date:
        where_clauses.append("p.created_at <= ?")
        params.append(to_date)

    # Tag filter (AND logic)
    tag_joins = ""
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for i, tag_name in enumerate(tag_list):
            tag_joins += f"""
                INNER JOIN photo_tags pt{i} ON p.id = pt{i}.photo_id
                INNER JOIN tags t{i} ON pt{i}.tag_id = t{i}.id AND t{i}.name = ?
            """
            params.append(tag_name)

    # Album filter (OR logic)
    if albums:
        album_list = [a.strip() for a in albums.split(",")]
        placeholders = ",".join(["?"] * len(album_list))
        where_clauses.append(f"""
            p.id IN (
                SELECT pa.photo_id FROM photo_albums pa
                INNER JOIN albums a ON pa.album_id = a.id
                WHERE a.name IN ({placeholders})
            )
        """)
        params.extend(album_list)

    # Build full query
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    with get_db() as conn:
        cursor = conn.cursor()

        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT p.id) as count
            FROM photos p
            {tag_joins}
            {where_sql}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()["count"]

        # Get paginated results
        search_query = f"""
            SELECT DISTINCT p.*
            FROM photos p
            {tag_joins}
            {where_sql}
            ORDER BY p.filename COLLATE NOCASE
            LIMIT ? OFFSET ?
        """
        cursor.execute(search_query, params + [limit, offset])

        photos = [dict(row) for row in cursor.fetchall()]

    total_pages = (total + limit - 1) // limit

    return PhotoList(
        photos=photos,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )
