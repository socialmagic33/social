from sqlalchemy.orm import Session
from typing import Optional, List
from app import models

def get_media_by_id(db: Session, media_id: int) -> Optional[models.Media]:
    return db.query(models.Media).filter(models.Media.id == media_id).first()

def get_user_media(db: Session, user_id: int) -> List[models.Media]:
    return db.query(models.Media).filter(models.Media.user_id == user_id).all()

def get_media_for_jobsite(db: Session, jobsite_id: int) -> List[models.Media]:
    return db.query(models.Media).filter(models.Media.jobsite_id == jobsite_id).all()

def get_media_for_grouping(db: Session, grouping_id: int) -> List[models.Media]:
    return db.query(models.Media).filter(models.Media.grouping_id == grouping_id).all()

def update_media(db: Session, media: models.Media, update_data: dict):
    for key, value in update_data.items():
        setattr(media, key, value)
    db.commit()
    db.refresh(media)
    return media

def delete_media(db: Session, media: models.Media):
    db.delete(media)
    db.commit()
