from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
from jose import JWTError, jwt
from app.core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    if ':' not in hashed_password:
        # Handle legacy plain text passwords
        return plain_password == hashed_password
    
    salt, stored_hash = hashed_password.split(':', 1)
    password_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
    return stored_hash == password_hash.hex()

def get_password_hash(password: str) -> str:
    """Hash a password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None