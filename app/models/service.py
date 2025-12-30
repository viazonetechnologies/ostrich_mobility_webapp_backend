from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class ServiceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ServicePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    product_serial_number = Column(String(100))
    issue_description = Column(Text, nullable=False)
    priority = Column(Enum(ServicePriority), default=ServicePriority.MEDIUM)
    status = Column(Enum(ServiceStatus), default=ServiceStatus.SCHEDULED)
    assigned_staff_id = Column(Integer, ForeignKey("users.id"))
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    service_notes = Column(Text)
    customer_feedback = Column(Text)
    rating = Column(Integer)  # 1-5 rating
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="service_tickets")
    assigned_staff = relationship("User", back_populates="service_tickets")
    schedules = relationship("ServiceSchedule", back_populates="ticket")

class ServiceSchedule(Base):
    __tablename__ = "service_schedules"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("service_tickets.id"))
    staff_id = Column(Integer, ForeignKey("users.id"))
    scheduled_date = Column(DateTime, nullable=False)
    location_latitude = Column(Numeric(10, 8))
    location_longitude = Column(Numeric(11, 8))
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    work_description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    ticket = relationship("ServiceTicket", back_populates="schedules")
    staff = relationship("User")