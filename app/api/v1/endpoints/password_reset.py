from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.core.sms import sms_service
from pydantic import BaseModel
import random
import string

router = APIRouter()

# In-memory OTP storage (use Redis in production)
otp_storage = {}

class RequestOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str
    new_password: str

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@router.post("/request-otp")
def request_otp(request: RequestOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this phone number not found"
        )
    
    otp = generate_otp()
    otp_storage[request.phone] = otp
    
    # Send OTP via SMS service
    sms_sent = sms_service.send_otp(request.phone, otp)
    
    if not sms_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again."
        )
    
    # For development: Return OTP in response (remove in production)
    import os
    if os.getenv('ENVIRONMENT', 'development') == 'development':
        return {"message": f"OTP sent to {request.phone}", "otp": otp}
    
    return {"message": f"OTP sent to {request.phone}"}

@router.post("/verify-otp")
def verify_otp_and_reset(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    stored_otp = otp_storage.get(request.phone)
    if not stored_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP request found for this phone number"
        )
    
    if stored_otp != request.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    from app.core.security import get_password_hash
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    del otp_storage[request.phone]
    
    return {"message": "Password reset successfully"}
