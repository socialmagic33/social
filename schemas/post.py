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