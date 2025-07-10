from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
import enum

class PostStatus(str, enum.Enum):
    draft = "draft"
    not_scheduled = "not_scheduled"
    scheduled = "scheduled"
    published = "published"

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    jobsite_id = Column(Integer, ForeignKey("jobsites.id"))
    grouping_id = Column(Integer, ForeignKey("media_groupings.id"), unique=True)
    platform = Column(String, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)
    status = Column(Enum(PostStatus), default=PostStatus.not_scheduled)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="posts")
    jobsite = relationship("Jobsite", back_populates="posts")
    media_grouping = relationship("MediaGrouping", back_populates="post")