from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    specifications = Column(Text)
    warranty_period = Column(Integer, default=12)  # in months
    price = Column(Numeric(10, 2))
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    enquiries = relationship("Enquiry", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")