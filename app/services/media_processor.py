from celery import Celery
from typing import List, Optional
from sqlalchemy.orm import Session
from app import models
from app.db.session import get_db
from datetime import datetime

celery = Celery('media_processor', broker='redis://localhost:6379/0')

@celery.task
def process_media_async(jobsite_id: int):
    db = next(get_db())
    try:
        processor = MediaProcessor(db)
        grouping = processor.process_jobsite_media(jobsite_id)
        return grouping.id if grouping else None
    finally:
        db.close()

class MediaProcessor:
    def __init__(self, db: Session):
        self.db = db

    def create_grouping(self, jobsite_id: int, media_ids: List[int]) -> models.MediaGrouping:
        """Create a new media grouping and associate media items"""
        grouping = models.MediaGrouping(jobsite_id=jobsite_id)
        self.db.add(grouping)
        self.db.flush()

        # Associate media with grouping
        media_items = self.db.query(models.Media).filter(
            models.Media.id.in_(media_ids)
        ).all()
        
        for media in media_items:
            media.grouping_id = grouping.id
        
        self.db.commit()
        self.db.refresh(grouping)
        return grouping

    def get_best_media_combinations(self, jobsite_id: int) -> List[List[models.Media]]:
        """Get optimal combinations of media for posts"""
        media_items = self.db.query(models.Media).filter_by(
            jobsite_id=jobsite_id,
            grouping_id=None
        ).all()

        combinations = []

        before_items = [m for m in media_items if m.status == "before"]
        after_items = [m for m in media_items if m.status == "after"]
        videos = [m for m in media_items if m.file_url.lower().endswith(('.mp4', '.mov'))]

        for before in before_items:
            for after in after_items:
                combo = [before, after]
                # Just pick the first available video (no rating logic)
                matching_video = videos[0] if videos else None
                if matching_video:
                    combo.append(matching_video)
                combinations.append(combo)

        return combinations

    def process_jobsite_media(self, jobsite_id: int) -> Optional[models.MediaGrouping]:
        """Process media for a jobsite and create optimal groupings"""
        combinations = self.get_best_media_combinations(jobsite_id)
        if not combinations:
            return None

        # Use the first (best) combination
        best_combo = combinations[0]
        media_ids = [m.id for m in best_combo]
        
        return self.create_grouping(jobsite_id, media_ids)
