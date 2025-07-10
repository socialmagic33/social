from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import enum

class MediaStatus(enum.Enum):
    BEFORE = "before"
    IN_PROGRESS = "in_progress"
    AFTER = "after"

class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    file_url = Column(String, nullable=False)
    description = Column(String)
    notes = Column(String)
    star_rating = Column(Integer)
    earliest_upload = Column(String)
    status = Column(Enum(MediaStatus), nullable=False)
    processed_urls = Column(JSON, default={})
    metadata = Column(JSON, default={})

    user_id = Column(Integer, ForeignKey("users.id"))
    jobsite_id = Column(Integer, ForeignKey("jobsites.id"))
    grouping_id = Column(Integer, ForeignKey("media_groupings.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="media")
    jobsite = relationship("Jobsite", back_populates="media")
    grouping = relationship("MediaGrouping", back_populates="media")