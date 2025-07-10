from pydantic import BaseModel
from typing import Optional
from enum import Enum

class MediaStatus(str, Enum):
    before = "before"
    in_progress = "in_progress"
    after = "after"

class MediaCreate(BaseModel):
    jobsite_address: str
    description: Optional[str] = ""
    notes: Optional[str] = ""
    star_rating: int
    earliest_upload: str = "ASAP"
    status: MediaStatus

class MediaOut(BaseModel):
    id: int
    file_url: str
    description: Optional[str]
    notes: Optional[str]
    star_rating: int
    earliest_upload: str
    status: MediaStatus
    jobsite_address: str

    class Config:
        orm_mode = True