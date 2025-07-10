from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import models
from app.core.security import get_password_hash, verify_password, create_access_token
from app.services.email import send_password_reset_email
import uuid
from datetime import datetime, timedelta

def register_user(db: Session, email: str, password: str):
    if db.query(models.User).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    token = str(uuid.uuid4())
    user = models.User(
        email=email,
        hashed_password=get_password_hash(password),
        verification_token=token
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, token

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return user

def generate_token(user: models.User):
    return create_access_token(data={"sub": str(user.id)})

def initiate_password_reset(db: Session, email: str):
    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        return  # Don't reveal if email exists
    
    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    send_password_reset_email(email, reset_token)

def validate_reset_token(db: Session, token: str):
    user = db.query(models.User).filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return user

def reset_password(db: Session, token: str, new_password: str):
    user = validate_reset_token(db, token)
    
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return user