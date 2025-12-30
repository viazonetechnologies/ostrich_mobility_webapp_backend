from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.region import Region

router = APIRouter()

@router.get("/", response_model=List[dict])
def read_regions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    regions = db.query(Region).offset(skip).limit(limit).all()
    return [
        {
            "id": region.id,
            "name": region.name,
            "code": region.code,
            "state": region.state,
            "country": region.country,
            "is_active": region.is_active,
            "manager_id": region.manager_id,
            "manager_name": f"{region.manager.first_name} {region.manager.last_name}" if region.manager else None,
            "created_at": region.created_at.isoformat() if region.created_at else None
        }
        for region in regions
    ]

@router.post("/", response_model=dict)
def create_region(
    region_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_region = Region(
        name=region_data["name"],
        code=region_data["code"],
        state=region_data["state"],
        country=region_data.get("country", "India"),
        is_active=region_data.get("is_active", True),
        manager_id=region_data.get("manager_id")
    )
    
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    
    return {
        "id": db_region.id,
        "name": db_region.name,
        "code": db_region.code,
        "state": db_region.state,
        "country": db_region.country,
        "is_active": db_region.is_active,
        "manager_id": db_region.manager_id,
        "created_at": db_region.created_at.isoformat() if db_region.created_at else None
    }

@router.put("/{region_id}", response_model=dict)
def update_region(
    region_id: int,
    region_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    for field, value in region_data.items():
        if hasattr(region, field):
            setattr(region, field, value)
    
    db.commit()
    db.refresh(region)
    
    return {
        "id": region.id,
        "name": region.name,
        "code": region.code,
        "state": region.state,
        "country": region.country,
        "is_active": region.is_active,
        "manager_id": region.manager_id,
        "created_at": region.created_at.isoformat() if region.created_at else None
    }

@router.delete("/{region_id}")
def delete_region(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    db.delete(region)
    db.commit()
    return {"message": "Region deleted successfully"}