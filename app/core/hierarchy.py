from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User

# Role hierarchy levels (higher number = higher authority)
ROLE_HIERARCHY = {
    'service_staff': 1,
    'sales_executive': 2,
    'manager': 3,
    'regional_officer': 4,
    'admin': 5,
    'super_admin': 6
}

def get_role_level(role: str) -> int:
    return ROLE_HIERARCHY.get(role, 0)

def can_manage_user(manager_role: str, target_role: str) -> bool:
    """Check if manager can manage target user based on hierarchy"""
    return get_role_level(manager_role) > get_role_level(target_role)

def get_manageable_roles(user_role: str) -> List[str]:
    """Get list of roles that user can manage"""
    user_level = get_role_level(user_role)
    return [role for role, level in ROLE_HIERARCHY.items() if level < user_level]

def get_subordinate_users(db: Session, manager: User) -> List[User]:
    """Get all users that manager can manage based on hierarchy and creation chain"""
    if manager.role.value == 'super_admin':
        return db.query(User).all()
    
    manageable_roles = get_manageable_roles(manager.role.value)
    
    # Get users created by this manager or their subordinates
    subordinates = []
    
    def get_created_users(creator_id: int):
        created = db.query(User).filter(User.created_by == creator_id).all()
        for user in created:
            if user.role.value in manageable_roles:
                subordinates.append(user)
                get_created_users(user.id)  # Recursive for chain
    
    get_created_users(manager.id)
    return subordinates

def can_view_user(viewer: User, target: User) -> bool:
    """Check if viewer can view target user"""
    if viewer.role.value == 'super_admin':
        return True
    
    if viewer.id == target.id:  # Can always view self
        return True
        
    return can_manage_user(viewer.role.value, target.role.value)

def can_edit_user(editor: User, target: User) -> bool:
    """Check if editor can edit target user"""
    if editor.role.value == 'super_admin':
        return True
        
    if editor.id == target.id:  # Can edit self (limited fields)
        return True
        
    # Can edit if created by editor or editor has higher role
    return (target.created_by == editor.id or 
            can_manage_user(editor.role.value, target.role.value))

def can_delete_user(deleter: User, target: User) -> bool:
    """Check if deleter can delete target user"""
    if deleter.role.value == 'super_admin':
        return True
        
    # Cannot delete self
    if deleter.id == target.id:
        return False
        
    # Can delete if created by deleter and has lower role
    return (target.created_by == deleter.id and 
            can_manage_user(deleter.role.value, target.role.value))