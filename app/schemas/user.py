from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
from app.core.validators import validate_phone, validate_email

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    role: UserRole
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., min_length=10, max_length=17)
    region: Optional[str] = Field(None, max_length=100)
    
    @validator('email')
    def validate_email_format(cls, v):
        return validate_email(str(v))
    
    @validator('phone')
    def validate_phone_format(cls, v):
        return validate_phone(v)
    

    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v.replace(' ', '').isalpha():
            raise ValueError('Name must contain only letters and spaces')
        return v.title()
    
    @validator('username')
    def validate_username(cls, v):
        return v.lower()

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, min_length=10, max_length=17)
    region: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    

    
    @validator('phone')
    def validate_phone_format(cls, v):
        if v:
            return validate_phone(v)
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v and not v.replace(' ', '').isalpha():
            raise ValueError('Name must contain only letters and spaces')
        return v.title() if v else v

class UserResponse(UserBase):
    id: int
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"