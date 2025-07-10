from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class MediaGrouping(Base):
    __tablename__ = "media_groupings"

    id = Column(Integer, primary_key=True, index=True)
    jobsite_id = Column(Integer, ForeignKey("jobsites.id"))
    generated_caption = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    jobsite = relationship("Jobsite", back_populates="media_groupings")
    media = relationship("Media", back_populates="grouping")
    post = relationship("Post", back_populates="media_grouping", uselist=False)