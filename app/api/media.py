from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List
from app.api.deps.auth import get_current_user
from app.models import User, Media, MediaFile
from app.db.session import get_db
from app.schemas.media import MediaCreate, MediaOut
from app.services.media import handle_upload_and_create_media, get_media_by_id, delete_media

router = APIRouter()

@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    jobsite_address: str = Form(...),
    description: str = Form(""),
    notes: str = Form(""),
    star_rating: int = Form(...),
    earliest_upload: str = Form("ASAP"),
    status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate star rating
    if not 1 <= star_rating <= 5:
        raise HTTPException(
            status_code=400,
            detail="Star rating must be between 1 and 5"
        )

    media_data = MediaCreate(
        jobsite_address=jobsite_address,
        description=description,
        notes=notes,
        star_rating=star_rating,
        earliest_upload=earliest_upload,
        status=status
    )
    
    return await handle_upload_and_create_media(file, media_data, current_user, db)

@router.get("/", response_model=List[MediaOut])
def list_media(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    media_items = db.query(Media).filter_by(user_id=current_user.id).all()
    return [
        MediaOut(
            id=media.id,
            file_url=media.file_url,
            description=media.description,
            notes=media.notes,
            star_rating=media.star_rating,
            earliest_upload=media.earliest_upload,
            status=media.status,
            jobsite_address=media.jobsite.address if media.jobsite else ""
        )
        for media in media_items
    ]

@router.get("/{media_id}", response_model=MediaOut)
def get_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    media = get_media_by_id(media_id, db)
    if not media or media.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Media not found")
    
    return MediaOut(
        id=media.id,
        file_url=media.file_url,
        description=media.description,
        notes=media.notes,
        star_rating=media.star_rating,
        earliest_upload=media.earliest_upload,
        status=media.status,
        jobsite_address=media.jobsite.address if media.jobsite else ""
    )

@router.delete("/{media_id}")
def delete_media_endpoint(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    media = get_media_by_id(media_id, db)
    if not media or media.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Media not found")
    
    delete_media(media, db)
    return {"message": "Media deleted successfully"}

@router.get("/files/{file_id}")
def serve_file(file_id: str, db: Session = Depends(get_db)):
    """Serve media files from database"""
    file_record = db.query(MediaFile).filter_by(id=file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    return Response(
        content=file_record.file_data,
        media_type=file_record.content_type,
        headers={
            "Content-Disposition": f"inline; filename={file_record.original_filename}",
            "Cache-Control": "public, max-age=3600"
        }
    )