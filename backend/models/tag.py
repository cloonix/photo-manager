"""Pydantic models for tags."""

from typing import List
from pydantic import BaseModel


class TagBase(BaseModel):
    """Base tag model."""
    id: str
    name: str


class TagCreate(BaseModel):
    """Request to create a tag."""
    name: str


class TagUpdate(BaseModel):
    """Request to update a tag."""
    name: str


class Tag(TagBase):
    """Full tag model with photo count."""
    photo_count: int = 0


class AddPhotosRequest(BaseModel):
    """Request to add photos to a tag."""
    photo_ids: List[str]
