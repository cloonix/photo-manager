"""EXIF metadata extraction service."""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import rawpy


def extract_exif_data(file_path: Path) -> Dict[str, Optional[str]]:
    """
    Extract EXIF metadata from an image file.

    Args:
        file_path: Path to image file

    Returns:
        Dictionary containing EXIF metadata
    """
    metadata = {
        "camera_make": None,
        "camera_model": None,
        "lens_model": None,
        "focal_length": None,
        "aperture": None,
        "shutter_speed": None,
        "iso": None,
        "date_taken": None,
        "gps_latitude": None,
        "gps_longitude": None,
    }

    try:
        # Check if it's a RAW file
        raw_extensions = {'.arw', '.cr2', '.cr3', '.nef', '.dng', '.orf', '.raf', '.rw2'}
        if file_path.suffix.lower() in raw_extensions:
            return _extract_raw_exif(file_path, metadata)
        
        # Handle regular image files with PIL
        with Image.open(file_path) as img:
            exif_data = img.getexif()

            if not exif_data:
                return metadata

            # Extract basic EXIF tags
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)

                if tag == "Make":
                    metadata["camera_make"] = str(value).strip()
                elif tag == "Model":
                    metadata["camera_model"] = str(value).strip()
                elif tag == "LensModel":
                    metadata["lens_model"] = str(value).strip()
                elif tag == "FocalLength":
                    metadata["focal_length"] = _format_focal_length(value)
                elif tag == "FNumber":
                    metadata["aperture"] = _format_aperture(value)
                elif tag == "ExposureTime":
                    metadata["shutter_speed"] = _format_shutter_speed(value)
                elif tag == "ISOSpeedRatings" or tag == "ISO":
                    metadata["iso"] = int(value) if value else None
                elif tag == "DateTimeOriginal" or tag == "DateTime":
                    metadata["date_taken"] = _parse_exif_datetime(value)

            # Extract GPS data if available
            gps_info = exif_data.get_ifd(0x8825)  # GPS IFD tag
            if gps_info:
                gps_data = {}
                for tag_id, value in gps_info.items():
                    tag = GPSTAGS.get(tag_id, tag_id)
                    gps_data[tag] = value

                # Parse GPS coordinates
                lat, lon = _parse_gps_coordinates(gps_data)
                metadata["gps_latitude"] = lat
                metadata["gps_longitude"] = lon

    except Exception as e:
        # Silently fail for unsupported formats or corrupted files
        print(f"Warning: Could not extract EXIF from {file_path}: {e}")

    return metadata


def _extract_raw_exif(file_path: Path, metadata: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    """
    Extract EXIF metadata from RAW image files using rawpy.

    Args:
        file_path: Path to RAW image file
        metadata: Dictionary to populate with metadata

    Returns:
        Dictionary containing EXIF metadata
    """
    try:
        with rawpy.imread(str(file_path)) as raw:
            # Get the embedded EXIF data
            exif_data = raw.raw_image_visible.copy()  # This triggers metadata loading
            
            # Access metadata through rawpy's metadata interface
            if hasattr(raw, 'raw_metadata'):
                raw_meta = raw.raw_metadata
                
                # Camera info
                metadata["camera_make"] = raw_meta.get('make', '').strip() if raw_meta.get('make') else None
                metadata["camera_model"] = raw_meta.get('model', '').strip() if raw_meta.get('model') else None
                
                # Exposure settings
                if raw_meta.get('iso_speed'):
                    metadata["iso"] = int(raw_meta['iso_speed'])
                if raw_meta.get('shutter'):
                    metadata["shutter_speed"] = f"1/{int(1/raw_meta['shutter'])}" if raw_meta['shutter'] < 1 else f"{raw_meta['shutter']:.2f}s"
                if raw_meta.get('aperture'):
                    metadata["aperture"] = f"f/{raw_meta['aperture']:.1f}"
                if raw_meta.get('focal_len'):
                    metadata["focal_length"] = f"{raw_meta['focal_len']:.1f}mm"
                if raw_meta.get('timestamp'):
                    metadata["date_taken"] = datetime.fromtimestamp(raw_meta['timestamp']).isoformat()
            
            # Try to extract EXIF from embedded preview
            try:
                thumb = raw.extract_thumb()
                if thumb.format == rawpy.ThumbFormat.JPEG:
                    import io
                    with Image.open(io.BytesIO(thumb.data)) as img:
                        exif_data = img.getexif()
                        if exif_data:
                            for tag_id, value in exif_data.items():
                                tag = TAGS.get(tag_id, tag_id)
                                
                                if tag == "Make" and not metadata["camera_make"]:
                                    metadata["camera_make"] = str(value).strip()
                                elif tag == "Model" and not metadata["camera_model"]:
                                    metadata["camera_model"] = str(value).strip()
                                elif tag == "LensModel":
                                    metadata["lens_model"] = str(value).strip()
                                elif tag == "FocalLength" and not metadata["focal_length"]:
                                    metadata["focal_length"] = _format_focal_length(value)
                                elif tag == "FNumber" and not metadata["aperture"]:
                                    metadata["aperture"] = _format_aperture(value)
                                elif tag == "ExposureTime" and not metadata["shutter_speed"]:
                                    metadata["shutter_speed"] = _format_shutter_speed(value)
                                elif (tag == "ISOSpeedRatings" or tag == "ISO") and not metadata["iso"]:
                                    metadata["iso"] = int(value) if value else None
                                elif (tag == "DateTimeOriginal" or tag == "DateTime") and not metadata["date_taken"]:
                                    metadata["date_taken"] = _parse_exif_datetime(value)
                            
                            # Extract GPS from embedded preview
                            gps_info = exif_data.get_ifd(0x8825)
                            if gps_info:
                                gps_data = {}
                                for tag_id, value in gps_info.items():
                                    tag = GPSTAGS.get(tag_id, tag_id)
                                    gps_data[tag] = value
                                lat, lon = _parse_gps_coordinates(gps_data)
                                metadata["gps_latitude"] = lat
                                metadata["gps_longitude"] = lon
            except Exception:
                pass  # Thumbnail extraction failed, continue with available data
                
    except Exception as e:
        print(f"Warning: Could not extract EXIF from RAW file {file_path}: {e}")
    
    return metadata


def _format_focal_length(value) -> Optional[str]:
    """Format focal length value."""
    try:
        if isinstance(value, tuple):
            focal = value[0] / value[1] if value[1] != 0 else value[0]
        else:
            focal = float(value)
        return f"{focal:.1f}mm"
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def _format_aperture(value) -> Optional[str]:
    """Format aperture (f-number) value."""
    try:
        if isinstance(value, tuple):
            f_num = value[0] / value[1] if value[1] != 0 else value[0]
        else:
            f_num = float(value)
        return f"f/{f_num:.1f}"
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def _format_shutter_speed(value) -> Optional[str]:
    """Format shutter speed value."""
    try:
        if isinstance(value, tuple):
            speed = value[0] / value[1] if value[1] != 0 else value[0]
        else:
            speed = float(value)

        if speed < 1:
            return f"1/{int(1/speed)}"
        else:
            return f"{speed:.1f}s"
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def _parse_exif_datetime(value: str) -> Optional[str]:
    """
    Parse EXIF datetime string to ISO format.

    Args:
        value: EXIF datetime string (YYYY:MM:DD HH:MM:SS)

    Returns:
        ISO formatted datetime string or None
    """
    try:
        # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
        dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
        return dt.isoformat()
    except (ValueError, TypeError):
        return None


def _parse_gps_coordinates(gps_data: dict) -> tuple[Optional[float], Optional[float]]:
    """
    Parse GPS coordinates from EXIF GPS data.

    Args:
        gps_data: Dictionary containing GPS tags

    Returns:
        Tuple of (latitude, longitude) or (None, None)
    """
    try:
        lat = gps_data.get("GPSLatitude")
        lat_ref = gps_data.get("GPSLatitudeRef")
        lon = gps_data.get("GPSLongitude")
        lon_ref = gps_data.get("GPSLongitudeRef")

        if not all([lat, lat_ref, lon, lon_ref]):
            return None, None

        # Convert degrees, minutes, seconds to decimal
        latitude = _convert_to_degrees(lat)
        if lat_ref == "S":
            latitude = -latitude

        longitude = _convert_to_degrees(lon)
        if lon_ref == "W":
            longitude = -longitude

        return latitude, longitude

    except Exception:
        return None, None


def _convert_to_degrees(value) -> float:
    """
    Convert GPS coordinate from degrees, minutes, seconds to decimal degrees.

    Args:
        value: Tuple of (degrees, minutes, seconds)

    Returns:
        Decimal degrees
    """
    d = float(value[0]) if isinstance(value[0], (int, float)) else value[0][0] / value[0][1]
    m = float(value[1]) if isinstance(value[1], (int, float)) else value[1][0] / value[1][1]
    s = float(value[2]) if isinstance(value[2], (int, float)) else value[2][0] / value[2][1]

    return d + (m / 60.0) + (s / 3600.0)
