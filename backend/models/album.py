"""Pydantic models for albums."""

from typing import Optional, List
from pydantic import BaseModel


class AlbumBase(BaseModel):
    """Base album model."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None


class AlbumCreate(BaseModel):
    """Request to create an album."""
    name: str
    description: Optional[str] = None


class AlbumUpdate(BaseModel):
    """Request to update an album."""
    name: Optional[str] = None
    description: Optional[str] = None


class Album(AlbumBase):
    """Full album model with photo count."""
    photo_count: Optional[int] = 0


class AlbumWithPhotos(AlbumBase):
    """Album with list of photo IDs."""
    photo_ids: List[str]


class AddPhotosRequest(BaseModel):
    """Request to add photos to an album."""
    photo_ids: List[str]
