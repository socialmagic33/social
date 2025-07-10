from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import magic
from typing import List
import asyncio
import logging

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'video/mp4',
    'video/quicktime',
    'video/webm'
]

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_SIZE = 1024 * 1024  # 1MB

class UploadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/media/upload" and request.method == "POST":
            # Check content length header
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_FILE_SIZE:
                logger.warning(f"File size exceeds limit: {content_length} bytes")
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB"
                )

            # Log upload attempt
            logger.info(f"File upload attempt from {request.client.host}")

        response = await call_next(request)

        # Log upload result
        if request.url.path == "/api/media/upload" and request.method == "POST":
            if response.status_code == 200:
                logger.info("File upload successful")
            else:
                logger.warning(f"File upload failed with status {response.status_code}")

        return response

    async def validate_file_content(self, file_content: bytes) -> bool:
        """Validate file content type"""
        try:
            content_type = magic.from_buffer(file_content[:2048], mime=True)
            return content_type in ALLOWED_MIME_TYPES
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False

    async def cleanup_failed_upload(self, file_path: str):
        """Cleanup failed uploads after timeout"""
        try:
            await asyncio.sleep(3600)  # Wait 1 hour
            # Implementation would check if upload completed and cleanup if not
            logger.info(f"Cleanup check for {file_path}")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

class FileValidationMiddleware(BaseHTTPMiddleware):
    """Additional file validation middleware"""
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/media/files/"):
            # Add security headers for file serving
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            return response
        
        return await call_next(request)