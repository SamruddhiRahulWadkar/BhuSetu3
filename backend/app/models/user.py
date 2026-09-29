import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="reviewer")  # admin, supervisor, verifier, operator, auditor, readonly_api
    is_active = Column(Boolean, default=True)
    api_key = Column(String(100), unique=True, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
