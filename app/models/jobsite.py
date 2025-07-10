from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class Jobsite(Base):
    __tablename__ = "jobsites"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="jobsites")
    media = relationship("Media", back_populates="jobsite", cascade="all, delete-orphan")
    media_groupings = relationship("MediaGrouping", back_populates="jobsite", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="jobsite", cascade="all, delete-orphan")