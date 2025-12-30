from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import datetime
from app.models.enquiry import EnquiryStatus

class EnquiryBase(BaseModel):
    customer_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=10000)
    message: Optional[str] = Field(None, max_length=2000)
    follow_up_date: Optional[datetime] = None
    
    @validator('message')
    def validate_message(cls, v):
        return v.strip() if v else v

class EnquiryCreate(EnquiryBase):
    pass

class EnquiryUpdate(BaseModel):
    product_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, gt=0, le=10000)
    message: Optional[str] = Field(None, max_length=2000)
    status: Optional[EnquiryStatus] = None
    assigned_to: Optional[int] = Field(None, gt=0)
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('message', 'notes')
    def validate_text_fields(cls, v):
        return v.strip() if v else v
    


class EnquiryResponse(EnquiryBase):
    id: int
    enquiry_number: str
    status: EnquiryStatus
    assigned_to: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True