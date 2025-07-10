import logging
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Log request
        logger.info(
            f"Request {request_id} started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", ""),
            }
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Request {request_id} completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 3),
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request {request_id} failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time": round(process_time, 3),
                },
                exc_info=True
            )
            raise

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Log security-related events"""
    
    async def dispatch(self, request: Request, call_next):
        # Log authentication attempts
        if request.url.path in ["/api/auth/login", "/api/auth/register"]:
            client_ip = request.client.host
            logger.info(
                f"Authentication attempt from {client_ip}",
                extra={
                    "event_type": "auth_attempt",
                    "endpoint": request.url.path,
                    "client_ip": client_ip,
                }
            )
        
        # Log file uploads
        if request.url.path == "/api/media/upload" and request.method == "POST":
            logger.info(
                "File upload attempt",
                extra={
                    "event_type": "file_upload",
                    "client_ip": request.client.host,
                }
            )
        
        response = await call_next(request)
        
        # Log failed authentication
        if request.url.path in ["/api/auth/login"] and response.status_code == 401:
            logger.warning(
                "Failed authentication attempt",
                extra={
                    "event_type": "auth_failure",
                    "client_ip": request.client.host,
                }
            )
        
        return response