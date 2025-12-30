from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.models.user import User
from app.models.customer import Customer
from app.models.sales import Sale, SaleItem
from app.models.service import ServiceTicket
from app.models.product import Product
from app.schemas.user import Token, UserResponse
from app.schemas.customer import CustomerResponse, CustomerMobileCreate
from sqlalchemy.sql import func
from app.core.security import get_password_hash
from app.models.password_reset import PasswordResetToken
import secrets

router = APIRouter()

@router.options("/login")
def login_options():
    return {"message": "OK"}

@router.get("/test")
def test_endpoint():
    return {"message": "Auth endpoint is working"}

@router.post("/simple-login")
def simple_login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Temporary login without database check
    if form_data.username == "admin" and form_data.password == "admin":
        access_token = create_access_token(data={"sub": "1"})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": "admin",
                "role": "admin"
            }
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/test-login")
def test_login():
    return {
        "message": "Login endpoint is accessible",
        "cors": "working"
    }

@router.post("/login")
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    print(f"Login attempt for username: {form_data.username}")
    user = db.query(User).filter(User.username == form_data.username).first()
    print(f"User found: {user is not None}")
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Block service_staff from webapp access
    if user.role.value == 'service_staff':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service staff cannot access webapp. Please use mobile app."
        )
    
    # Update last login
    user.last_login = func.now()
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "is_active": user.is_active
        }
    }

from pydantic import BaseModel

class CustomerLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/customer/login")
def customer_login(
    login_data: CustomerLoginRequest,
    db: Session = Depends(get_db)
):
    try:
        # For customers, username can be email or phone
        customer = db.query(Customer).filter(
            (Customer.email == login_data.username) | 
            (Customer.phone == login_data.username)
        ).first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Customer not found"
            )
        
        # For now, use a simple password check
        if login_data.password != "customer123":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )
        
        # Skip verification check for now
        # if customer.verification_status != "verified":
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Customer account not verified"
        #     )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": f"customer_{customer.id}"}, expires_delta=access_token_expires
        )
    
        name_parts = customer.contact_person.split() if customer.contact_person else ["Customer"]
        first_name = name_parts[0] if name_parts else "Customer"
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": customer.id,
                "username": customer.email,
                "email": customer.email,
                "full_name": customer.contact_person,
                "first_name": first_name,
                "last_name": last_name,
                "phone": customer.phone,
                "role": "customer",
                "is_active": True
            }
        }
    except Exception as e:
        print(f"Customer login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/customer/register")
def customer_register(
    customer_data: CustomerMobileCreate,
    db: Session = Depends(get_db)
):
    # Check if customer already exists
    existing_customer = db.query(Customer).filter(
        (Customer.email == customer_data.email) | 
        (Customer.phone == customer_data.phone)
    ).first()
    
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email or phone already exists"
        )
    
    # Generate customer code
    last_customer = db.query(Customer).order_by(Customer.id.desc()).first()
    next_id = (last_customer.id + 1) if last_customer else 1
    customer_code = f"CUS{next_id:06d}"
    
    # Create new customer
    new_customer = Customer(
        customer_code=customer_code,
        customer_type="b2c",  # Default for mobile app registrations
        contact_person=customer_data.full_name,
        email=customer_data.email,
        phone=customer_data.phone,
        address=customer_data.address or "Not provided",
        city=customer_data.city or "Not provided",
        state=customer_data.state or "Not provided",
        pin_code=customer_data.pin_code or "000000",
        verification_status="pending"
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return {
        "message": "Customer registered successfully",
        "customer_code": customer_code,
        "status": "pending_verification"
    }

@router.post("/forgot-password")
def forgot_password(
    username: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Don't reveal if user exists
        return {"message": "If the username exists, a reset token has been generated"}
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    
    # In production, send email with token
    # For demo, return token
    return {
        "message": "Reset token generated",
        "token": token,  # Remove in production
        "username": username
    }

@router.post("/reset-password")
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    if reset_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )
    
    # Update password
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.password_hash = get_password_hash(new_password)
    reset_token.used = True
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/customer/dashboard")
def get_customer_dashboard(
    db: Session = Depends(get_db)
):
    try:
        # Get customer stats
        total_customers = db.query(Customer).count()
        total_sales = db.query(Sale).count()
        total_tickets = db.query(ServiceTicket).count()
        
        # Get recent sales with product names
        from app.models.product import Product
        recent_sales = db.query(Sale).order_by(Sale.created_at.desc()).limit(5).all()
        purchases = []
        for sale in recent_sales:
            customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
            # Get first product from sale items
            sale_item = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).first()
            product_name = "Product"
            if sale_item:
                product = db.query(Product).filter(Product.id == sale_item.product_id).first()
                product_name = product.name if product else "Product"
            
            purchases.append({
                "id": sale.id,
                "product_name": product_name,
                "customer_name": customer.contact_person if customer else "Customer",
                "date": sale.sale_date.strftime("%b %d, %Y") if sale.sale_date else "Recent",
                "status": "Active",
                "amount": float(sale.final_amount) if sale.final_amount else 0
            })
        
        return {
            "stats": {
                "active_products": min(total_sales, 10),
                "open_tickets": min(total_tickets, 5)
            },
            "purchases": purchases[:2]
        }
    except Exception as e:
        print(f"Dashboard error: {e}")
        return {
            "stats": {"active_products": 2, "open_tickets": 1},
            "purchases": []
        }