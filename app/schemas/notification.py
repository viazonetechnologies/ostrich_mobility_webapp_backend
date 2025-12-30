from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.notification import NotificationType

class NotificationBase(BaseModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    send_via_sms: bool = False
    send_via_email: bool = False
    scheduled_at: Optional[datetime] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool = False
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True