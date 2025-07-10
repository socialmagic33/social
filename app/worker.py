from celery import Celery
from app.config import settings

celery = Celery(
    'tasks',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1
)

@celery.task(bind=True, max_retries=3)
def process_media(self, media_id: int):
    try:
        from app.services.media_processor import MediaProcessor
        processor = MediaProcessor()
        processor.process_media(media_id)
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * 5)  # Retry in 5 minutes

@celery.task(bind=True, max_retries=3)
def schedule_posts(self, user_id: int):
    try:
        from app.services.post_scheduler import schedule_posts_for_user
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            schedule_posts_for_user(user_id, db)
        finally:
            db.close()
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * 5)