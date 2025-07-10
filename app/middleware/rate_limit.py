from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
import time
import asyncio
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.limits = {
            "auth": {"requests": 5, "window": 60},     # 5 auth requests per minute
            "media": {"requests": 20, "window": 60},   # 20 media requests per minute
            "api": {"requests": 100, "window": 60}     # 100 general API requests per minute
        }
        # Clean up old entries every 5 minutes
        asyncio.create_task(self._cleanup_task())

    async def is_rate_limited(self, key: str, endpoint_type: str) -> bool:
        now = time.time()
        window = self.limits[endpoint_type]["window"]
        max_requests = self.limits[endpoint_type]["requests"]
        
        # Clean old requests
        cutoff = now - window
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= max_requests:
            return True
        
        # Add current request
        self.requests[key].append(now)
        return False

    async def _cleanup_task(self):
        """Periodically clean up old entries"""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            try:
                now = time.time()
                keys_to_remove = []
                
                for key, requests in self.requests.items():
                    # Remove requests older than 1 hour
                    cutoff = now - 3600
                    self.requests[key] = [req_time for req_time in requests if req_time > cutoff]
                    
                    # Remove empty entries
                    if not self.requests[key]:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.requests[key]
                    
            except Exception as e:
                logger.error(f"Rate limiter cleanup error: {str(e)}")

# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for static files and health check
    if request.url.path.startswith(("/static/", "/health", "/docs", "/redoc")):
        return await call_next(request)

    # Get client identifier
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    key = f"ip:{client_ip}"
    
    # Determine endpoint type
    if request.url.path.startswith("/api/auth"):
        endpoint_type = "auth"
    elif request.url.path.startswith("/api/media"):
        endpoint_type = "media"
    else:
        endpoint_type = "api"
    
    # Check rate limit
    if await rate_limiter.is_rate_limited(key, endpoint_type):
        logger.warning(
            f"Rate limit exceeded for {client_ip}",
            extra={
                "client_ip": client_ip,
                "endpoint_type": endpoint_type,
                "path": request.url.path
            }
        )
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": "60"}
        )
    
    return await call_next(request)

class RedisRateLimiter:
    """Redis-based rate limiter for production"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.limits = {
            "auth": {"requests": 5, "window": 60},
            "media": {"requests": 20, "window": 60},
            "api": {"requests": 100, "window": 60}
        }

    async def is_rate_limited(self, key: str, endpoint_type: str) -> bool:
        now = int(time.time())
        window = self.limits[endpoint_type]["window"]
        max_requests = self.limits[endpoint_type]["requests"]
        
        redis_key = f"rate_limit:{endpoint_type}:{key}:{now // window}"
        
        try:
            # Increment request count
            current = await self.redis.incr(redis_key)
            
            # Set expiration if first request
            if current == 1:
                await self.redis.expire(redis_key, window)
            
            return current > max_requests
        except Exception as e:
            logger.error(f"Redis rate limiter error: {str(e)}")
            # Fail open - don't block requests if Redis is down
            return False