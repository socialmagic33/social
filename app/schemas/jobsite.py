from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class JobsiteBase(BaseModel):
    address: str

class JobsiteCreate(JobsiteBase):
    pass

class JobsiteUpdate(JobsiteBase):
    pass

class JobsiteOut(JobsiteBase):
    id: int
    created_at: datetime
    user_id: int

    class Config:
        orm_mode = True

class JobsiteWithStats(JobsiteOut):
    media_count: int = 0
    posts_count: int = 0
    last_activity: Optional[datetime] = None