from pydantic import BaseModel, validator, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.core.validators import validate_positive_number, validate_percentage, validate_future_date

class SaleItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=10000)
    unit_price: Decimal = Field(..., gt=0)
    serial_number: Optional[str] = Field(None, max_length=100)
    
    @validator('unit_price')
    def validate_unit_price(cls, v):
        return validate_positive_number(float(v))

class SaleItemResponse(SaleItemCreate):
    id: int
    total_price: Decimal
    warranty_start_date: Optional[datetime] = None
    warranty_end_date: Optional[datetime] = None
    is_warranty_active: bool = True
    product_name: Optional[str] = None

    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    customer_id: int = Field(..., gt=0)
    sale_date: datetime
    total_amount: Decimal = Field(..., gt=0)
    discount_percentage: Decimal = Field(default=0, ge=0, le=100)
    discount_amount: Decimal = Field(default=0, ge=0)
    final_amount: Decimal = Field(..., gt=0)
    delivery_address: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('total_amount', 'final_amount')
    def validate_amounts(cls, v):
        return validate_positive_number(float(v))
    
    @validator('discount_percentage')
    def validate_discount_percent(cls, v):
        return validate_percentage(float(v))
    
    @validator('sale_date')
    def validate_sale_date(cls, v):
        if v > datetime.now():
            raise ValueError('Sale date cannot be in the future')
        return v

class SaleCreate(SaleBase):
    items: List[SaleItemCreate] = []  # Make items optional with default empty list
    payment_status: Optional[str] = "pending"
    delivery_status: Optional[str] = "pending"
    delivery_date: Optional[datetime] = None

class SaleResponse(SaleBase):
    id: int
    sale_number: str
    payment_status: str = "pending"
    delivery_status: str = "pending"
    delivery_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[SaleItemResponse] = []
    customer_name: Optional[str] = None
    created_by_name: Optional[str] = None

    class Config:
        from_attributes = True