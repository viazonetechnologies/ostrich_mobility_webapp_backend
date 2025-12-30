from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class EnquiryStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUOTED = "quoted"
    CONVERTED = "converted"
    CLOSED = "closed"

class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(Integer, primary_key=True, index=True)
    enquiry_number = Column(String(20), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    message = Column(Text)
    status = Column(Enum(EnquiryStatus), default=EnquiryStatus.NEW)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    follow_up_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="enquiries")
    product = relationship("Product", back_populates="enquiries")
    assigned_user = relationship("User")