from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_number = Column(String(20), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    sale_date = Column(DateTime, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    final_amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(20), default="pending")
    delivery_status = Column(String(20), default="pending")
    delivery_date = Column(DateTime)
    delivery_address = Column(String(500))
    notes = Column(String(1000))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="sales")
    creator = relationship("User")
    items = relationship("SaleItem", back_populates="sale")

class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    serial_number = Column(String(100))
    warranty_start_date = Column(DateTime)
    warranty_end_date = Column(DateTime)
    is_warranty_active = Column(Boolean, default=True)

    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")