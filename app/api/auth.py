from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.services import auth as auth_service
from app.services.session import session_manager
from app.db.session import get_db

router = APIRouter()

@router.post("/register")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user, token = auth_service.register_user(db, user_in.email, user_in.password)
    return {
        "message": "User registered. Check your email to verify.",
        "user_id": user.id,
        "verification_token": token
    }

@router.post("/login")
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, user_in.email, user_in.password)
    tokens = session_manager.create_tokens(user.id)
    return tokens

@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    return session_manager.refresh_tokens(refresh_token, db)