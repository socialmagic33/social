import os
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app import models
from app.schemas.media import MediaCreate
from app.db.crud.jobsite import get_or_create_jobsite
from app.services.storage import storage

async def handle_upload_and_create_media(file: UploadFile, data: MediaCreate, user: models.User, db: Session):
    # Upload file to S3
    file_url = await storage.upload_file(file, folder=f"user_{user.id}")
    
    # Get or create jobsite
    jobsite = get_or_create_jobsite(db, user, data.jobsite_address)

    # Create media record
    media = models.Media(
        file_url=file_url,
        description=data.description,
        notes=data.notes,
        star_rating=data.star_rating,
        earliest_upload=data.earliest_upload,
        status=data.status,
        jobsite_id=jobsite.id,
        user_id=user.id
    )
    db.add(media)
    db.commit()
    db.refresh(media)

    return {"message": "Media uploaded", "media_id": media.id, "file_url": file_url}