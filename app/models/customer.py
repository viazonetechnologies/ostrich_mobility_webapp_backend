from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class CustomerType(str, enum.Enum):
    b2c = "b2c"
    b2b = "b2b"
    b2g = "b2g"

class VerificationStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(20), unique=True, index=True, nullable=False)
    customer_type = Column(Enum(CustomerType), nullable=False)
    company_name = Column(String(200))
    contact_person = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), default="India")
    pin_code = Column(String(10), nullable=False)
    tax_id = Column(String(50))
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.pending)
    verification_document_url = Column(String(500))
    assigned_sales_executive = Column(Integer, ForeignKey("users.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    sales_executive = relationship("User", foreign_keys=[assigned_sales_executive], back_populates="assigned_customers")
    creator = relationship("User", foreign_keys=[created_by])
    enquiries = relationship("Enquiry", back_populates="customer")
    sales = relationship("Sale", back_populates="customer")
    service_tickets = relationship("ServiceTicket", back_populates="customer")