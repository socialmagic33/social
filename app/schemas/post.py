from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    draft = "draft"
    not_scheduled = "not_scheduled"
    scheduled = "scheduled"
    published = "published"

class Platform(str, Enum):
    facebook = "facebook"
    instagram = "instagram"
    nextdoor = "nextdoor"

class PostCreate(BaseModel):
    grouping_id: int
    platform: Optional[str] = "instagram"
    scheduled_for: Optional[datetime] = None
    caption: Optional[str] = None

class PostUpdate(BaseModel):
    scheduled_for: Optional[datetime] = None
    caption: Optional[str] = None
    status: Optional[PostStatus] = None

class PostOut(BaseModel):
    id: int
    status: PostStatus
    platform: Optional[str]
    scheduled_for: Optional[datetime]
    created_at: datetime
    grouping_id: int
    jobsite_id: int

    class Config:
        orm_mode = True

class PostWithDetails(PostOut):
    jobsite_address: Optional[str] = None
    media_count: int = 0
    caption: Optional[str] = None