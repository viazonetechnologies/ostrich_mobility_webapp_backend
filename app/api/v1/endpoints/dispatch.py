from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.dispatch import Dispatch
from app.models.sales import Sale
from app.schemas.dispatch import DispatchCreate, DispatchUpdate, DispatchResponse

router = APIRouter()

@router.get("/", response_model=List[DispatchResponse])
def read_dispatches(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dispatches = db.query(Dispatch).offset(skip).limit(limit).all()
    
    for dispatch in dispatches:
        # Set customer information
        if dispatch.customer:
            dispatch.customer_name = dispatch.customer.contact_person
        
        # Set product information
        if dispatch.product:
            dispatch.product_name = dispatch.product.name
    
    return dispatches

@router.post("/", response_model=DispatchResponse)
def create_dispatch(
    dispatch: DispatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if customer exists
    from app.models.customer import Customer
    customer = db.query(Customer).filter(Customer.id == dispatch.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Check if product exists
    from app.models.product import Product
    product = db.query(Product).filter(Product.id == dispatch.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Generate dispatch number
    last_dispatch = db.query(Dispatch).order_by(Dispatch.id.desc()).first()
    next_id = (last_dispatch.id + 1) if last_dispatch else 1
    dispatch_number = f"DSP{next_id:06d}"
    
    db_dispatch = Dispatch(
        dispatch_number=dispatch_number,
        **dispatch.model_dump()
    )
    
    db.add(db_dispatch)
    db.commit()
    db.refresh(db_dispatch)
    return db_dispatch

@router.get("/{dispatch_id}", response_model=DispatchResponse)
def read_dispatch(
    dispatch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispatch not found"
        )
    
    # Set customer information
    if dispatch.customer:
        dispatch.customer_name = dispatch.customer.contact_person
    
    # Set product information
    if dispatch.product:
        dispatch.product_name = dispatch.product.name
    
    return dispatch

@router.put("/{dispatch_id}", response_model=DispatchResponse)
def update_dispatch(
    dispatch_id: int,
    dispatch_update: DispatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispatch not found"
        )
    
    update_data = dispatch_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dispatch, field, value)
    
    db.commit()
    db.refresh(dispatch)
    return dispatch

@router.delete("/{dispatch_id}")
def delete_dispatch(
    dispatch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispatch not found"
        )
    
    db.delete(dispatch)
    db.commit()
    return {"message": "Dispatch deleted successfully"}
