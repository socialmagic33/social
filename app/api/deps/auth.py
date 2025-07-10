from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.db.session import get_db
from app import models
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_token_from_cookie_or_header(request: Request, token: str = Depends(oauth2_scheme)):
    """Get token from Authorization header or cookie"""
    if token:
        return token
    
    # Try to get token from cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token and cookie_token.startswith("Bearer "):
        return cookie_token[7:]  # Remove "Bearer " prefix
    
    return None

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_cookie_or_header)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    user = db.query(models.User).get(user_id)
    if user is None:
        raise credentials_exception
    return user

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_cookie_or_header)
):
    """Get current user but don't raise exception if not authenticated"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            return None
    except (JWTError, TypeError, ValueError):
        return None

    user = db.query(models.User).get(user_id)
    return user