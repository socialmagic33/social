from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
from typing import List
import logging

logger = logging.getLogger(__name__)

class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        secret_key: str,
        safe_methods: List[str] = None,
        cookie_name: str = "csrftoken",
        header_name: str = "X-CSRF-Token",
        exempt_paths: List[str] = None
    ):
        super().__init__(app)
        self.secret_key = secret_key
        self.safe_methods = safe_methods or ["GET", "HEAD", "OPTIONS"]
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.exempt_paths = exempt_paths or [
            "/docs", "/redoc", "/openapi.json", "/health",
            "/static/", "/api/auth/login", "/api/auth/register"
        ]

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Skip CSRF for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)
            
            # Set CSRF token cookie if not present
            if self.cookie_name not in request.cookies:
                token = secrets.token_urlsafe(32)
                response.set_cookie(
                    self.cookie_name,
                    token,
                    httponly=True,
                    samesite="strict",
                    secure=True,
                    max_age=3600  # 1 hour
                )
            return response

        # For unsafe methods, validate CSRF token
        csrf_token = request.cookies.get(self.cookie_name)
        header_token = request.headers.get(self.header_name)

        if not csrf_token:
            logger.warning(f"CSRF token missing in cookie for {request.url.path}")
            raise HTTPException(
                status_code=403,
                detail="CSRF token missing"
            )

        if not header_token:
            logger.warning(f"CSRF token missing in header for {request.url.path}")
            raise HTTPException(
                status_code=403,
                detail="CSRF token missing in header"
            )

        if csrf_token != header_token:
            logger.warning(f"CSRF token mismatch for {request.url.path}")
            raise HTTPException(
                status_code=403,
                detail="CSRF token invalid"
            )

        return await call_next(request)

def get_csrf_token(request: Request) -> str:
    """Get CSRF token from request"""
    return request.cookies.get("csrftoken", "")

# Template function to include CSRF token in templates
def csrf_token():
    """Template function to get CSRF token"""
    return secrets.token_urlsafe(32)