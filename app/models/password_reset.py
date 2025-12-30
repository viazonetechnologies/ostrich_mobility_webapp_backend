from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timedelta
from app.db.database import Base

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    token = Column(String(100), unique=True, index=True)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
