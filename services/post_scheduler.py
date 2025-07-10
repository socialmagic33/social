from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models

# Existing create_post_from_grouping remains here...

# Define posting frequency rules by user plan
PLAN_POSTING_RULES = {
    "free_trial": 2,     # 2 per week
    "starter": 4,
    "premium": 7,
}

def schedule_posts_for_user(user_id: int, db: Session):
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
        post.scheduled_for = next_slot
        post.status = "scheduled"
        next_slot += timedelta(days=interval_days)
        db.add(post)

    db.commit()