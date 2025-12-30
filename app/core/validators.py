import re
from typing import Optional
from datetime import datetime
from pydantic import validator, EmailStr

def validate_phone(phone: str) -> str:
    """Validate phone number format: +[country code][digits] or 10-digit Indian number"""
    phone = phone.strip()
    
    # Remove spaces, hyphens, parentheses
    cleaned = re.sub(r'[\s\-\(\)]+', '', phone)
    
    # Check for international format (+country code)
    if cleaned.startswith('+'):
        digits = cleaned[1:]
        if not digits.isdigit():
            raise ValueError('Please enter a valid phone number')
        if not 10 <= len(digits) <= 15:
            raise ValueError('Please enter a valid phone number')
        return cleaned
    
    # Check for Indian 10-digit format
    if cleaned.isdigit() and len(cleaned) == 10:
        if not cleaned.startswith(('6', '7', '8', '9')):
            raise ValueError('Please enter a valid phone number')
        return cleaned
    
    raise ValueError('Please enter a valid phone number')

def validate_email(email: str) -> str:
    """Validate email format: must have @ and domain extension"""
    if '@' not in email:
        raise ValueError('Please enter a valid email address')
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError('Please enter a valid email address')
    
    return email.lower()

def validate_pin_code(pin_code: str) -> str:
    """Validate Indian PIN code"""
    if not re.match(r'^\d{6}$', pin_code):
        raise ValueError('Please enter a valid PIN code')
    return pin_code

def validate_future_date(date_value: Optional[datetime]) -> Optional[datetime]:
    """Validate that date is not in the past"""
    if date_value and date_value.replace(tzinfo=None) < datetime.now():
        raise ValueError('Please select a future date')
    return date_value

def validate_positive_number(value: float) -> float:
    """Validate positive numbers"""
    if value <= 0:
        raise ValueError('Please enter a positive value')
    return value

def validate_percentage(value: float) -> float:
    """Validate percentage (0-100)"""
    if not 0 <= value <= 100:
        raise ValueError('Please enter a percentage between 0 and 100')
    return value