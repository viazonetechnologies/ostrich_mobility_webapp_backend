from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from datetime import datetime
from app.models.customer import CustomerType, VerificationStatus
from app.core.validators import validate_phone, validate_email, validate_pin_code

class CustomerBase(BaseModel):
    customer_type: CustomerType
    company_name: Optional[str] = Field(None, max_length=200)
    contact_person: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=17)
    address: str = Field(..., min_length=10, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    country: str = Field(default="India", max_length=100)
    pin_code: str = Field(..., min_length=6, max_length=10)
    tax_id: Optional[str] = Field(None, max_length=50)
    
    @validator('phone')
    def validate_phone_format(cls, v):
        return validate_phone(v)
    
    @validator('email')
    def validate_email_format(cls, v):
        return validate_email(str(v))
    
    @validator('pin_code')
    def validate_pin_format(cls, v):
        return validate_pin_code(v)
    
    @validator('contact_person', 'city', 'state')
    def validate_names(cls, v):
        if not v.replace(' ', '').isalpha():
            raise ValueError('Must contain only letters and spaces')
        return v.title()

class CustomerCreate(CustomerBase):
    pass

class CustomerMobileCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None

class CustomerUpdate(BaseModel):
    customer_type: Optional[CustomerType] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pin_code: Optional[str] = None
    tax_id: Optional[str] = None
    verification_status: Optional[VerificationStatus] = None
    assigned_sales_executive: Optional[int] = None

class CustomerResponse(CustomerBase):
    id: int
    customer_code: str
    verification_status: VerificationStatus
    verification_document_url: Optional[str] = None
    assigned_sales_executive: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True