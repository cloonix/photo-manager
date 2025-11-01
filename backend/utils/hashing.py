"""SHA256 hashing utilities for photo identification."""

import hashlib
from pathlib import Path


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256 = hashlib.sha256()

    # Read file in chunks to handle large files efficiently
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()
