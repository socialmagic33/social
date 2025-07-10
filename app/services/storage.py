import os
import uuid
import magic
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app import models
from typing import Optional
import base64

class DatabaseStorage:
    """Store media files directly in the database"""
    
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/quicktime', 'video/webm'
        ]

    async def upload_file(self, file: UploadFile, folder: str = "") -> str:
        """Upload a file and store it in the database"""
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {self.max_file_size/1024/1024}MB"
            )
        
        # Validate file type
        content_type = magic.from_buffer(content, mime=True)
        if content_type not in self.allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {content_type} not allowed"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = self._get_extension(file.filename or "file")
        filename = f"{file_id}{file_extension}"
        
        # Create file record in database
        file_record = models.MediaFile(
            id=file_id,
            filename=filename,
            original_filename=file.filename,
            content_type=content_type,
            file_size=len(content),
            file_data=content
        )
        
        # Note: We'll need to pass the database session to this method
        # For now, return a URL that points to our file serving endpoint
        return f"/api/media/files/{file_id}"

    def delete_file(self, file_url: str, db: Session):
        """Delete a file from the database"""
        try:
            # Extract file ID from URL
            file_id = file_url.split("/")[-1]
            
            file_record = db.query(models.MediaFile).filter_by(id=file_id).first()
            if file_record:
                db.delete(file_record)
                db.commit()
                
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")

    def get_file(self, file_id: str, db: Session) -> Optional[models.MediaFile]:
        """Get file record from database"""
        return db.query(models.MediaFile).filter_by(id=file_id).first()

    def _get_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''

# Create storage instance
storage = DatabaseStorage()