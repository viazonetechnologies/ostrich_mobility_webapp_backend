from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.hierarchy import (
    can_view_user, can_edit_user, can_delete_user, 
    get_subordinate_users, get_manageable_roles
)

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Super admin and admin see all users
    if current_user.role.value in ['super_admin', 'admin']:
        users = db.query(User).offset(skip).limit(limit).all()
    # Regional officer sees users in their region
    elif current_user.role.value == 'regional_officer':
        users = db.query(User).filter(User.region == current_user.region).offset(skip).limit(limit).all()
    # Manager sees users in their region
    elif current_user.role.value == 'manager':
        users = db.query(User).filter(User.region == current_user.region).offset(skip).limit(limit).all()
    # Sales executive cannot access users page
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view users"
        )
    return users

@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Sales executives cannot create users
    if current_user.role.value == 'sales_executive':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sales executives cannot create users"
        )
    
    target_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    manageable_roles = get_manageable_roles(current_user.role.value)
    
    if target_role not in manageable_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot create user with role {target_role}"
        )
    
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=get_password_hash(user.password),
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        region=user.region,
        created_by=current_user.id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not can_view_user(current_user, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not can_edit_user(current_user, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this user"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    
    if current_user.id == user.id and "role" in update_data:
        del update_data["role"]
    
    if "role" in update_data:
        target_role = update_data["role"].value if hasattr(update_data["role"], 'value') else str(update_data["role"])
        manageable_roles = get_manageable_roles(current_user.role.value)
        if target_role not in manageable_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot assign role {target_role}"
            )
    
    if "password" in update_data:
        if current_user.role.value != 'super_admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin can change passwords. Use forgot password for password reset."
            )
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not can_delete_user(current_user, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.get("/manageable-roles/", response_model=List[str])
def get_user_manageable_roles(
    current_user: User = Depends(get_current_user)
):
    # Sales executives cannot manage any roles
    if current_user.role.value == 'sales_executive':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view manageable roles"
        )
    return get_manageable_roles(current_user.role.value)