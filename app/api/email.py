from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import email as email_service
from app.core.security import create_access_token
from app.db.crud.user import get_user_by_verification_token, verify_user_email
from app import models

router = APIRouter()

@router.post("/send-verification")
async def send_verification_email(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        background_tasks.add_task(
            email_service.send_verification_email,
            email,
            db
        )
        return {"message": "Verification email sent"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/verify/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    user = get_user_by_verification_token(db, token)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )
    
    verify_user_email(db, user)
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "message": "Email verified successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/resend-verification")
async def resend_verification_email(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If an account exists with this email, a verification email will be sent"}
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    try:
        background_tasks.add_task(
            email_service.send_verification_email,
            email,
            db
        )
        return {"message": "Verification email sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send verification email")