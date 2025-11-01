"""EXIF metadata extraction service."""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


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
