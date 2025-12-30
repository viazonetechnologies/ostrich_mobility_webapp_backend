from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class NotificationType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    ERROR = "error"
    PROMOTION = "promotion"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.INFO)
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    send_via_sms = Column(Boolean, default=False)
    send_via_email = Column(Boolean, default=False)
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")
    customer = relationship("Customer")