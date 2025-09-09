"""
Database base module.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)  # UUID string
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(String, nullable=True)     # store Celery task ID
    status = Column(String, default="pending")  # optional: pending, done, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())