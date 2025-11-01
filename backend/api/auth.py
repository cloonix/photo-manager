"""Authentication API endpoints."""

import logging
import os

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse

from backend.auth import oauth, check_authentication
from backend.config import config
from authlib.integrations.starlette_client import OAuthError


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def login(request: Request):
    """Redirect to OIDC provider for authentication."""
    if not config.OIDC_CLIENT_ID:
        raise HTTPException(
            status_code=400,
            detail="OIDC authentication not configured"
        )
    
    redirect_uri = config.OIDC_REDIRECT_URI or request.url_for('callback')
    return await oauth.oidc.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(request: Request):
    """Handle OIDC callback after authentication."""
    try:
        token = await oauth.oidc.authorize_access_token(request)
        user_info = token.get('userinfo')
        request.session['user'] = user_info
        return RedirectResponse("/")
    except OAuthError as e:
        logging.warning(f"OAuth error during callback: {type(e).__name__}")
        raise HTTPException(status_code=400, detail="Authentication failed")
    except Exception as e:
        logging.error(f"Unexpected error during auth callback: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Authentication service temporarily unavailable"
        )


@router.post("/logout")
async def logout(request: Request):
    """Clear user session."""
    request.session.clear()
    return {"ok": True}


@router.get("/me")
async def me(request: Request):
    """Get current authentication status."""
    authenticated = check_authentication(request)
    user = request.session.get('user') if authenticated else None
    
    return {
        "authenticated": authenticated,
        "user": user
    }
