from sqlalchemy import Column, String, Integer, LargeBinary, DateTime
from app.db.base import Base
from datetime import datetime

class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(String, primary_key=True)  # UUID
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    content_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)