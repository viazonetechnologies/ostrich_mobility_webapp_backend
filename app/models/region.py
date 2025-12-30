from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), default="India")
    is_active = Column(Boolean, default=True)
    manager_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    manager = relationship("User")
    service_centers = relationship("ServiceCenter", back_populates="region")

class ServiceCenter(Base):
    __tablename__ = "service_centers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pin_code = Column(String(10), nullable=False)
    phone = Column(String(15), nullable=False)
    email = Column(String(100))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    region_id = Column(Integer, ForeignKey("regions.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    region = relationship("Region", back_populates="service_centers")