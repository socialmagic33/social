from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models

# Define posting frequency rules by user plan
PLAN_POSTING_RULES = {
    "free_trial": 2,     # 2 per week
    "starter": 4,        # 4 per week
    "premium": 7,        # Daily posts
}

def create_post_from_grouping(grouping: models.MediaGrouping, user: models.User, db: Session):
    """Create a post from a media grouping"""
    post = models.Post(
        user_id=user.id,
        jobsite_id=grouping.jobsite_id,
        grouping_id=grouping.id,
        platform="instagram",
        status="not_scheduled"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def schedule_posts_for_user(user_id: int, db: Session):
    """Schedule unscheduled posts based on user's plan and existing schedule"""
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise ValueError("User not found")

    max_per_week = PLAN_POSTING_RULES.get(user.plan, 2)
    interval_days = 7 / max_per_week

    # Get user's already scheduled posts (sorted by scheduled date)
    scheduled = db.query(models.Post).filter(
        models.Post.user_id == user_id,
        models.Post.status == "scheduled"
    ).order_by(models.Post.scheduled_for.asc()).all()

    # Start from the last scheduled time or now
    last_scheduled = scheduled[-1].scheduled_for if scheduled else datetime.utcnow()
    next_slot = last_scheduled + timedelta(days=interval_days)

    # Get posts that are not yet scheduled
    unscheduled = db.query(models.Post).filter(
        models.Post.user_id == user_id,
        models.Post.status == "not_scheduled"
    ).order_by(models.Post.created_at.asc()).all()

    for post in unscheduled:
        # Check earliest upload date constraint
        media_items = db.query(models.Media).filter_by(grouping_id=post.grouping_id).all()
        earliest_dates = [m.earliest_upload for m in media_items if m.earliest_upload]
        
        if earliest_dates:
            earliest_allowed = max(earliest_dates)
            if earliest_allowed == "1_week" and next_slot < datetime.utcnow() + timedelta(days=7):
                next_slot = datetime.utcnow() + timedelta(days=7)
            elif earliest_allowed == "2_weeks" and next_slot < datetime.utcnow() + timedelta(days=14):
                next_slot = datetime.utcnow() + timedelta(days=14)
            elif earliest_allowed == "1_month" and next_slot < datetime.utcnow() + timedelta(days=30):
                next_slot = datetime.utcnow() + timedelta(days=30)

        post.scheduled_for = next_slot
        post.status = "scheduled"
        next_slot += timedelta(days=interval_days)
        db.add(post)

    db.commit()