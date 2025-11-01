"""Shared FastAPI dependencies."""

from fastapi import Request, HTTPException
from backend.config import config


def auth(request: Request) -> bool:
    """
    Check if user is authenticated via OIDC session or DEV_MODE.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if authenticated
        
    Raises:
        HTTPException: If authentication is required but not configured
    """
    if not config.OIDC_CLIENT_ID and not config.DEV_MODE:
        raise HTTPException(status_code=401, detail="Authentication required - OIDC not configured")
    return config.DEV_MODE or request.session.get('user') is not None
