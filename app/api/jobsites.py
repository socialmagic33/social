from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models import User, Jobsite
from app.schemas.jobsite import JobsiteCreate, JobsiteOut
from app.api.deps.auth import get_current_user
from app.db.crud.jobsite import get_or_create_jobsite

router = APIRouter()

@router.post("/", response_model=JobsiteOut)
def create_jobsite(
    jobsite: JobsiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobsite_db = get_or_create_jobsite(db, current_user, jobsite.address)
    return JobsiteOut(
        id=jobsite_db.id,
        address=jobsite_db.address,
        created_at=jobsite_db.created_at,
        user_id=jobsite_db.user_id
    )

@router.get("/", response_model=List[JobsiteOut])
def list_jobsites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobsites = db.query(Jobsite).filter(Jobsite.user_id == current_user.id).all()
    return [
        JobsiteOut(
            id=jobsite.id,
            address=jobsite.address,
            created_at=jobsite.created_at,
            user_id=jobsite.user_id
        )
        for jobsite in jobsites
    ]

@router.get("/{jobsite_id}", response_model=JobsiteOut)
def get_jobsite(
    jobsite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobsite = db.query(Jobsite).filter(
        Jobsite.id == jobsite_id,
        Jobsite.user_id == current_user.id
    ).first()
    if not jobsite:
        raise HTTPException(status_code=404, detail="Jobsite not found")
    
    return JobsiteOut(
        id=jobsite.id,
        address=jobsite.address,
        created_at=jobsite.created_at,
        user_id=jobsite.user_id
    )

@router.delete("/{jobsite_id}")
def delete_jobsite(
    jobsite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobsite = db.query(Jobsite).filter(
        Jobsite.id == jobsite_id,
        Jobsite.user_id == current_user.id
    ).first()
    if not jobsite:
        raise HTTPException(status_code=404, detail="Jobsite not found")
    
    db.delete(jobsite)
    db.commit()
    return {"message": "Jobsite deleted"}

@router.put("/{jobsite_id}", response_model=JobsiteOut)
def update_jobsite(
    jobsite_id: int,
    jobsite_update: JobsiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobsite = db.query(Jobsite).filter(
        Jobsite.id == jobsite_id,
        Jobsite.user_id == current_user.id
    ).first()
    if not jobsite:
        raise HTTPException(status_code=404, detail="Jobsite not found")
    
    jobsite.address = jobsite_update.address
    db.commit()
    db.refresh(jobsite)
    
    return JobsiteOut(
        id=jobsite.id,
        address=jobsite.address,
        created_at=jobsite.created_at,
        user_id=jobsite.user_id
    )