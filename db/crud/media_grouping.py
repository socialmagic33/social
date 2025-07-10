from sqlalchemy.orm import Session
from typing import Optional, List
from app import models

def create_grouping(db: Session, jobsite_id: int, caption: str = "") -> models.MediaGrouping:
    grouping = models.MediaGrouping(jobsite_id=jobsite_id, generated_caption=caption)
    db.add(grouping)
    db.commit()
    db.refresh(grouping)
    return grouping

def get_grouping_by_id(db: Session, grouping_id: int) -> Optional[models.MediaGrouping]:
    return db.query(models.MediaGrouping).filter_by(id=grouping_id).first()

def get_groupings_for_jobsite(db: Session, jobsite_id: int) -> List[models.MediaGrouping]:
    return db.query(models.MediaGrouping).filter_by(jobsite_id=jobsite_id).all()

def update_grouping_caption(db: Session, grouping: models.MediaGrouping, caption: str):
    grouping.generated_caption = caption
    db.commit()
    db.refresh(grouping)
    return grouping

def delete_grouping(db: Session, grouping: models.MediaGrouping):
    db.delete(grouping)
    db.commit()