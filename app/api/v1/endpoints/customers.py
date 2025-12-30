from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.customer import Customer

router = APIRouter()

def generate_customer_code(db: Session) -> str:
    # Get the highest customer code number
    customers = db.query(Customer.customer_code).filter(
        Customer.customer_code.like('CUS%')
    ).all()
    
    if not customers:
        return "CUS000001"
    
    max_number = 0
    for (code,) in customers:
        try:
            number = int(code[3:])
            max_number = max(max_number, number)
        except (ValueError, IndexError):
            continue
    
    return f"CUS{max_number + 1:06d}"

@router.get("/")
def read_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        customers = db.query(Customer).limit(100).all()
        result = []
        for customer in customers:
            result.append({
                "id": customer.id,
                "customer_code": customer.customer_code,
                "customer_type": str(customer.customer_type.value) if customer.customer_type else "b2c",
                "company_name": customer.company_name,
                "contact_person": customer.contact_person,
                "email": customer.email,
                "phone": customer.phone,
                "address": customer.address,
                "city": customer.city,
                "state": customer.state,
                "country": customer.country,
                "pin_code": customer.pin_code,
                "tax_id": customer.tax_id,
                "verification_status": str(customer.verification_status.value) if customer.verification_status else "pending",
                "verification_document_url": customer.verification_document_url,
                "assigned_sales_executive": customer.assigned_sales_executive,
                "created_at": str(customer.created_at) if customer.created_at else None,
                "updated_at": str(customer.updated_at) if customer.updated_at else None
            })
        return result
    except Exception as e:
        print(f"Error in customers endpoint: {e}")
        return []

@router.post("/")
def create_customer(
    customer_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate required fields
    required_fields = ['customer_type', 'contact_person', 'email', 'phone', 'address', 'city', 'state', 'pin_code']
    for field in required_fields:
        if not customer_data.get(field):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field} is required"
            )
    
    # Validate email format
    if '@' not in customer_data['email']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate phone format
    phone = customer_data['phone'].strip()
    # Remove spaces, hyphens, parentheses
    import re
    cleaned_phone = re.sub(r'[\s\-\(\)]+', '', phone)
    
    # Check if phone contains only digits and + (for international)
    if not re.match(r'^\+?[0-9]+$', cleaned_phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must contain only digits and optional + prefix"
        )
    
    # Validate phone length and format
    if cleaned_phone.startswith('+'):
        digits = cleaned_phone[1:]
        if not 10 <= len(digits) <= 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="International phone number must be 10-15 digits"
            )
    else:
        if len(cleaned_phone) != 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Indian phone number must be exactly 10 digits"
            )
        if not cleaned_phone.startswith(('6', '7', '8', '9')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Indian mobile number must start with 6, 7, 8, or 9"
            )
    
    # Update phone with cleaned version
    customer_data['phone'] = cleaned_phone
    
    # Check for duplicate email
    existing = db.query(Customer).filter(Customer.email == customer_data['email']).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists"
        )
    
    try:
        customer_code = generate_customer_code(db)
        
        db_customer = Customer(
            customer_code=customer_code,
            customer_type=customer_data["customer_type"],
            company_name=customer_data.get("company_name"),
            contact_person=customer_data["contact_person"],
            email=customer_data["email"],
            phone=customer_data["phone"],
            address=customer_data["address"],
            city=customer_data["city"],
            state=customer_data["state"],
            country=customer_data.get("country", "India"),
            pin_code=customer_data["pin_code"],
            tax_id=customer_data.get("tax_id"),
            created_by=current_user.id
        )
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        
        return {
            "id": db_customer.id,
            "customer_code": db_customer.customer_code,
            "message": "Customer created successfully"
        }
    except Exception as e:
        print(f"Error creating customer: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{customer_id}")
def read_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{customer_id}")
def update_customer(
    customer_id: int,
    customer_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    for key, value in customer_data.items():
        if hasattr(customer, key):
            setattr(customer, key, value)
    
    db.commit()
    db.refresh(customer)
    return {"message": "Customer updated successfully", "id": customer.id}

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(customer)
    db.commit()
    return {"message": "Customer deleted successfully"}
