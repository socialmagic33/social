import os
from fastapi import UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app import models
from app.schemas.media import MediaCreate
from app.db.crud.jobsite import get_or_create_jobsite
from app.services.storage import storage

async def handle_upload_and_create_media(
    file: UploadFile,
    data: MediaCreate,
    user: models.User,
    db: Session
) -> dict:
    try:
        # Upload file to database storage
        file_url = await upload_file_to_database(file, db)
        
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

        return {
            "message": "Media uploaded successfully",
            "media_id": media.id,
            "file_url": file_url
        }

    except Exception as e:
        # Cleanup on failure
        if 'file_url' in locals():
            try:
                storage.delete_file(file_url, db)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

async def upload_file_to_database(file: UploadFile, db: Session) -> str:
    """Upload file to database and return URL"""
    # Read file content
    content = await file.read()
    
    # Validate file size (50MB limit)
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum limit of {max_size/1024/1024}MB"
        )
    
    # Validate file type
    import magic
    content_type = magic.from_buffer(content, mime=True)
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'video/mp4', 'video/quicktime', 'video/webm'
    ]
    
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {content_type} not allowed"
        )
    
    # Generate unique ID
    import uuid
    file_id = str(uuid.uuid4())
    
    # Get file extension
    file_extension = ""
    if file.filename and '.' in file.filename:
        file_extension = '.' + file.filename.rsplit('.', 1)[1].lower()
    
    filename = f"{file_id}{file_extension}"
    
    # Create file record
    file_record = models.MediaFile(
        id=file_id,
        filename=filename,
        original_filename=file.filename,
        content_type=content_type,
        file_size=len(content),
        file_data=content
    )
    
    db.add(file_record)
    db.commit()
    
    return f"/api/media/files/{file_id}"

def get_media_by_id(media_id: int, db: Session) -> models.Media:
    """Get media by ID"""
    return db.query(models.Media).filter_by(id=media_id).first()

def delete_media(media: models.Media, db: Session):
    """Delete media and associated file"""
    try:
        # Delete file from storage
        storage.delete_file(media.file_url, db)
    except:
        pass  # Continue even if file deletion fails
    
    # Delete media record
    db.delete(media)
    db.commit()