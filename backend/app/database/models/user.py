from datetime import datetime

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import relationship

from ..base import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chats = relationship("Chat", back_populates="owner")
