from sqlalchemy.orm import Session
from typing import Optional, List
from app import models

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_verification_token(db: Session, token: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.verification_token == token).first()

def create_user(db: Session, email: str, hashed_password: str, verification_token: Optional[str]) -> models.User:
    user = models.User(
        email=email,
        hashed_password=hashed_password,
        verification_token=verification_token
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_user_email(db: Session, user: models.User):
    user.is_verified = True
    user.verification_token = None
    db.commit()
    db.refresh(user)
    return user

def update_user_profile(db: Session, user: models.User, company_name: str, values: str, specialties: str):
    user.company_name = company_name
    user.values = values
    user.specialties = specialties
    db.commit()
    db.refresh(user)
    return user

def update_user_plan(db: Session, user: models.User, plan: str):
    user.plan = plan
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).get(user_id)
    if user:
        db.delete(user)
        db.commit()
