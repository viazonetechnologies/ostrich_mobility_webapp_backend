from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    regional_officer = "regional_officer"
    manager = "manager"
    sales_executive = "sales_executive"
    service_staff = "service_staff"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(15), nullable=False)
    region = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User", remote_side=[id])
    assigned_customers = relationship("Customer", foreign_keys="Customer.assigned_sales_executive", back_populates="sales_executive")
    created_customers = relationship("Customer", foreign_keys="Customer.created_by")
    service_tickets = relationship("ServiceTicket", back_populates="assigned_staff")
    notifications = relationship("Notification", back_populates="user")