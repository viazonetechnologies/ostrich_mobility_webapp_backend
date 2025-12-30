from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.enquiry import Enquiry
from app.models.customer import Customer
from app.models.product import Product
from app.models.notification import Notification
from app.schemas.enquiry import EnquiryCreate, EnquiryUpdate, EnquiryResponse

router = APIRouter()

def generate_enquiry_number(db: Session) -> str:
    last_enquiry = db.query(Enquiry).order_by(Enquiry.id.desc()).first()
    if last_enquiry:
        last_number = int(last_enquiry.enquiry_number[3:])
        return f"ENQ{last_number + 1:06d}"
    return "ENQ000001"

@router.get("/", response_model=List[EnquiryResponse])
def read_enquiries(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Enquiry)
    
    if status_filter:
        query = query.filter(Enquiry.status == status_filter)
    
    enquiries = query.filter(Enquiry.product_id.isnot(None)).offset(skip).limit(limit).all()
    
    for enquiry in enquiries:
        if enquiry.customer:
            enquiry.customer_name = enquiry.customer.contact_person
        if enquiry.product:
            enquiry.product_name = enquiry.product.name
    
    return enquiries

@router.post("/", response_model=EnquiryResponse)
def create_enquiry(
    enquiry: EnquiryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate required fields
    if not enquiry.customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID is required"
        )
    
    if not enquiry.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID is required"
        )
    
    if enquiry.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than 0"
        )
    
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == enquiry.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Verify product exists
    product = db.query(Product).filter(Product.id == enquiry.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    enquiry_number = generate_enquiry_number(db)
    
    db_enquiry = Enquiry(
        enquiry_number=enquiry_number,
        **enquiry.dict()
    )
    
    db.add(db_enquiry)
    db.commit()
    db.refresh(db_enquiry)
    
    # Create notification for all users
    all_users = db.query(User).all()
    for user in all_users:
        notification = Notification(
            user_id=user.id,
            title="New Enquiry Received",
            message=f"New enquiry {enquiry_number} from {customer.contact_person} for {product.name}. Quantity: {enquiry.quantity}",
            type="info"
        )
        db.add(notification)
    db.commit()
    
    return db_enquiry

@router.get("/{enquiry_id}", response_model=EnquiryResponse)
def read_enquiry(
    enquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found"
        )
    
    if enquiry.customer:
        enquiry.customer_name = enquiry.customer.contact_person
    if enquiry.product:
        enquiry.product_name = enquiry.product.name
    
    return enquiry

@router.put("/{enquiry_id}", response_model=EnquiryResponse)
def update_enquiry(
    enquiry_id: int,
    enquiry_update: EnquiryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found"
        )
    
    update_data = enquiry_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(enquiry, field, value)
    
    db.commit()
    db.refresh(enquiry)
    return enquiry

@router.delete("/{enquiry_id}")
def delete_enquiry(
    enquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found"
        )
    
    db.delete(enquiry)
    db.commit()
    return {"message": "Enquiry deleted successfully"}