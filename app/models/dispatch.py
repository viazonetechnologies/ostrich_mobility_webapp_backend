from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.database import Base

class DispatchStatus(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"

class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_number = Column(String(50), unique=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    driver_name = Column(String(100))
    driver_phone = Column(String(20))
    vehicle_number = Column(String(50))
    status = Column(SQLEnum(DispatchStatus), default=DispatchStatus.pending)
    dispatch_date = Column(DateTime)
    estimated_delivery = Column(DateTime)
    actual_delivery = Column(DateTime, nullable=True)
    tracking_notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sale = relationship("Sale")
    customer = relationship("Customer")
    product = relationship("Product")
