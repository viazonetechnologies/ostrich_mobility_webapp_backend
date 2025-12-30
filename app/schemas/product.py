from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.core.validators import validate_positive_number

class ProductCategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('name')
    def validate_category_name(cls, v):
        return v.strip().title()

class ProductCategoryCreate(ProductCategoryBase):
    pass

class ProductCategoryResponse(ProductCategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = Field(None, gt=0)
    specifications: Optional[str] = Field(None, max_length=2000)
    warranty_period: int = Field(default=12, ge=0, le=120)
    price: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    
    @validator('name')
    def validate_product_name(cls, v):
        return v.strip().title()
    
    @validator('price')
    def validate_product_price(cls, v):
        if v is not None:
            return validate_positive_number(float(v))
        return v
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Image URL must start with http:// or https://')
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    specifications: Optional[str] = None
    warranty_period: Optional[int] = None
    price: Optional[Decimal] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    product_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategoryResponse] = None
    total_sales: Optional[int] = 0
    total_quantity: Optional[int] = 0
    purchased_quantity: Optional[int] = 0

    class Config:
        from_attributes = True