from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import models
from app.core.security import get_password_hash, verify_password, create_access_token

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
    return user, token  # return to

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return user
def generate_token(user: models.User):
    return create_access_token(data={"sub": str(user.id)})
