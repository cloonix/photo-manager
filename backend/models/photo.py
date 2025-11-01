"""Pydantic models for photos."""

from typing import Optional, List
from pydantic import BaseModel


class PhotoMetadata(BaseModel):
    """EXIF metadata for a photo."""
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    focal_length: Optional[str] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    iso: Optional[int] = None
    date_taken: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None


class PhotoBase(BaseModel):
    """Base photo model."""
    id: str
    file_path: str
    filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    indexed_at: Optional[str] = None


class Photo(PhotoBase):
    """Full photo model with metadata."""
    metadata: Optional[PhotoMetadata] = None


class PhotoList(BaseModel):
    """Paginated list of photos."""
    photos: List[PhotoBase]
    total: int
    page: int
    page_size: int
    total_pages: int


class MovePhotoRequest(BaseModel):
    """Request to move a photo."""
    folder_path: str


class RenamePhotoRequest(BaseModel):
    """Request to rename a photo."""
    new_filename: str
