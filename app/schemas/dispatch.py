from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional
from app.core.validators import validate_phone, validate_future_date

class DispatchBase(BaseModel):
    customer_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    driver_name: str = Field(..., min_length=2, max_length=100)
    driver_phone: str = Field(..., min_length=12, max_length=17)
    vehicle_number: str = Field(..., min_length=4, max_length=50)
    dispatch_date: datetime
    estimated_delivery: datetime
    tracking_notes: Optional[str] = Field(None, max_length=500)
    
    @validator('driver_phone')
    def validate_driver_phone(cls, v):
        return validate_phone(v)
    
    @validator('driver_name')
    def validate_driver_name(cls, v):
        if not v.replace(' ', '').isalpha():
            raise ValueError('Driver name must contain only letters and spaces')
        return v.title()
    
    @validator('vehicle_number')
    def validate_vehicle_number(cls, v):
        return v.upper().strip()
    
    @validator('estimated_delivery')
    def validate_delivery_date(cls, v, values):
        if 'dispatch_date' in values and v <= values['dispatch_date']:
            raise ValueError('Estimated delivery must be after dispatch date')
        return v

class DispatchCreate(DispatchBase):
    pass

class DispatchUpdate(BaseModel):
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    vehicle_number: Optional[str] = None
    status: Optional[str] = None
    dispatch_date: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    tracking_notes: Optional[str] = None

class DispatchResponse(DispatchBase):
    id: int
    dispatch_number: str
    status: str
    actual_delivery: Optional[datetime] = None
    created_at: datetime
    sale_number: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    
    class Config:
        from_attributes = True
