from sqlalchemy.orm import Session
from app import models
from typing import List, Optional

def get_or_create_jobsite(db: Session, user: models.User, address: str) -> models.Jobsite:
    """Get existing jobsite or create new one"""
    jobsite = db.query(models.Jobsite).filter_by(
        user_id=user.id, 
        address=address
    ).first()
    
    if not jobsite:
        jobsite = models.Jobsite(
            address=address, 
            user_id=user.id
        )
        db.add(jobsite)
        db.flush()
    
    return jobsite

def get_jobsite_by_id(db: Session, jobsite_id: int, user_id: int) -> Optional[models.Jobsite]:
    """Get jobsite by ID for specific user"""
    return db.query(models.Jobsite).filter_by(
        id=jobsite_id,
        user_id=user_id
    ).first()

def get_user_jobsites(db: Session, user_id: int) -> List[models.Jobsite]:
    """Get all jobsites for a user"""
    return db.query(models.Jobsite).filter_by(
        user_id=user_id
    ).order_by(models.Jobsite.created_at.desc()).all()

def update_jobsite(db: Session, jobsite: models.Jobsite, address: str) -> models.Jobsite:
    """Update jobsite address"""
    jobsite.address = address
    db.commit()
    db.refresh(jobsite)
    return jobsite

def delete_jobsite(db: Session, jobsite: models.Jobsite):
    """Delete jobsite and all associated data"""
    db.delete(jobsite)
    db.commit()

def get_jobsite_stats(db: Session, jobsite_id: int) -> dict:
    """Get statistics for a jobsite"""
    media_count = db.query(models.Media).filter_by(jobsite_id=jobsite_id).count()
    posts_count = db.query(models.Post).filter_by(jobsite_id=jobsite_id).count()
    
    # Get last activity (most recent media upload or post)
    last_media = db.query(models.Media).filter_by(
        jobsite_id=jobsite_id
    ).order_by(models.Media.created_at.desc()).first()
    
    last_post = db.query(models.Post).filter_by(
        jobsite_id=jobsite_id
    ).order_by(models.Post.created_at.desc()).first()
    
    last_activity = None
    if last_media and last_post:
        last_activity = max(last_media.created_at, last_post.created_at)
    elif last_media:
        last_activity = last_media.created_at
    elif last_post:
        last_activity = last_post.created_at
    
    return {
        "media_count": media_count,
        "posts_count": posts_count,
        "last_activity": last_activity
    }