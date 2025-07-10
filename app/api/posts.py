from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app import models
from app.schemas.post import PostOut
from app.services.post_scheduler import schedule_posts_for_user

router = APIRouter()

@router.get("/unpublished", response_model=List[PostOut])
def get_unpublished_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    posts = db.query(models.Post).filter(
        models.Post.user_id == current_user.id,
        models.Post.status.in_(["not_scheduled", "draft"])
    ).order_by(models.Post.created_at.asc()).all()
    return posts

@router.post("/schedule")
def schedule_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        schedule_posts_for_user(current_user.id, db)
        return {"message": "Posts scheduled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/process-media/{jobsite_id}")
def process_jobsite_media(
    jobsite_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify jobsite ownership
    jobsite = db.query(models.Jobsite).filter_by(
        id=jobsite_id,
        user_id=current_user.id
    ).first()
    if not jobsite:
        raise HTTPException(status_code=404, detail="Jobsite not found")

    processor = MediaProcessor(db)
    grouping = processor.process_jobsite_media(jobsite_id)
    
    if not grouping:
        raise HTTPException(
            status_code=400,
            detail="No suitable media combinations found"
        )
    
    return {"message": "Media processed successfully", "grouping_id": grouping.id}