"""Authentication module with OIDC support."""

import logging
import secrets
from typing import Optional

from fastapi import HTTPException, Request, Depends
from authlib.integrations.starlette_client import OAuth, OAuthError

from backend.config import config


# Initialize OAuth
oauth = OAuth()

# Register OIDC provider if configured
if config.OIDC_CLIENT_ID:
    oauth.register(
        'oidc',
        client_id=config.OIDC_CLIENT_ID,
        client_secret=config.OIDC_CLIENT_SECRET,
        server_metadata_url=config.OIDC_DISCOVERY_URL,
        client_kwargs={'scope': 'openid profile email'}
    )


def get_current_user(request: Request) -> Optional[dict]:
    """
    Get the current authenticated user from the session.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User info dict if authenticated, None otherwise
    """
    if not config.OIDC_CLIENT_ID and not config.DEV_MODE:
        raise HTTPException(
            status_code=401,
            detail="Authentication required - OIDC not configured"
        )
    
    # In dev mode, allow access without authentication
    if config.DEV_MODE:
        return {"dev_mode": True, "sub": "dev-user"}
    
    # Check session for authenticated user
    user = request.session.get('user')
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    return user


def check_authentication(request: Request) -> bool:
    """
    Check if the user is authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if authenticated, False otherwise
    """
    if config.DEV_MODE:
        return True
    
    return request.session.get('user') is not None
