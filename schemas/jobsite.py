from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class JobsiteBase(BaseModel):
    address: str

class JobsiteCreate(JobsiteBase):
    pass

class JobsiteOut(JobsiteBase):
    id: int
    created_at: datetime
    user_id: int

    class Config:
        orm_mode = True