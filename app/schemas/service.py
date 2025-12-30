from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import datetime
from app.models.service import ServiceStatus, ServicePriority

class ServiceTicketBase(BaseModel):
    customer_id: int = Field(..., gt=0)
    product_serial_number: Optional[str] = Field(None, max_length=100)
    issue_description: str = Field(..., min_length=10, max_length=2000)
    priority: ServicePriority = ServicePriority.MEDIUM
    scheduled_date: Optional[datetime] = None
    
    @validator('issue_description')
    def validate_issue_description(cls, v):
        return v.strip()
    
    @validator('product_serial_number')
    def validate_serial_number(cls, v):
        if v:
            return v.upper().strip()
        return v

class ServiceTicketCreate(ServiceTicketBase):
    pass

class ServiceTicketUpdate(BaseModel):
    issue_description: Optional[str] = Field(None, min_length=10, max_length=2000)
    priority: Optional[ServicePriority] = None
    status: Optional[ServiceStatus] = None
    assigned_staff_id: Optional[int] = Field(None, gt=0)
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    service_notes: Optional[str] = Field(None, max_length=2000)
    customer_feedback: Optional[str] = Field(None, max_length=1000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    

    
    @validator('service_notes', 'customer_feedback')
    def validate_text_fields(cls, v):
        return v.strip() if v else v

class ServiceTicketResponse(ServiceTicketBase):
    id: int
    ticket_number: str
    status: ServiceStatus
    assigned_staff_id: Optional[int] = None
    completed_date: Optional[datetime] = None
    service_notes: Optional[str] = None
    customer_feedback: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True