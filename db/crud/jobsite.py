from sqlalchemy.orm import Session
from app import models

def get_or_create_jobsite(db: Session, user: models.User, address: str):
    jobsite = db.query(models.Jobsite).filter_by(user_id=user.id, address=address).first()
    if not jobsite:
        jobsite = models.Jobsite(address=address, owner=user)
        db.add(jobsite)
        db.flush()
    return jobsite