from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base


class StorageObject(Base):
    __tablename__ = "storage_objects"

    id = Column(Integer, primary_key=True, index=True)
    bucket = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    path = Column(String(500), nullable=False)
    owner_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner = relationship("User")
