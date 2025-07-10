from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt, JWTError
from app.config import settings
from sqlalchemy.orm import Session
from app.models import User
import uuid
from redis import Redis

class SessionManager:
    def __init__(self):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.access_token_expire = timedelta(minutes=15)
        self.refresh_token_expire = timedelta(days=7)
        self.session_expire = timedelta(days=30)

    def create_tokens(self, user_id: int) -> dict:
        session_id = str(uuid.uuid4())
        access_token = self._create_token(
            {"sub": str(user_id), "sid": session_id, "type": "access"},
            self.access_token_expire
        )
        refresh_token = self._create_token(
            {"sub": str(user_id), "sid": session_id, "type": "refresh"},
            self.refresh_token_expire
        )

        # Store session in Redis
        self.redis.setex(
            f"session:{session_id}",
            int(self.session_expire.total_seconds()),
            str(user_id)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_tokens(self, refresh_token: str, db: Session) -> dict:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            session_id = payload.get("sid")
            if not self.redis.exists(f"session:{session_id}"):
                raise HTTPException(status_code=401, detail="Session expired")

            user_id = int(payload.get("sub"))
            return self.create_tokens(user_id)
            
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    def invalidate_session(self, session_id: str):
        self.redis.delete(f"session:{session_id}")

    def _create_token(self, data: dict, expires_delta: timedelta) -> str:
        expire = datetime.utcnow() + expires_delta
        to_encode = {**data, "exp": expire}
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    async def cleanup_expired_sessions(self):
        """Cleanup task to remove expired sessions"""
        for key in self.redis.scan_iter("session:*"):
            if not self.redis.ttl(key):
                self.redis.delete(key)

session_manager = SessionManager()