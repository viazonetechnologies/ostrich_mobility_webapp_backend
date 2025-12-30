from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.customer import Customer
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse

router = APIRouter()

@router.get("/test")
def test_endpoint():
    return {"message": "Test successful"}

@router.post("/test-post")
def test_post(
    title: str,
    message: str
):
    return {"message": f"Received: {title} - {message}"}

@router.post("/", response_model=NotificationResponse)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    db.commit()
    
    return {"message": "Notification marked as read"}

@router.put("/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": "All notifications marked as read"}

@router.get("/broadcast-simple")
def broadcast_simple(
    title: str,
    message: str,
    notification_type: str = "info"
):
    return {"message": f"Would broadcast: {title} - {message} ({notification_type})"}

@router.get("/send-simple/{customer_id}")
def send_simple(
    customer_id: int,
    title: str,
    message: str
):
    return {"message": f"Would send to customer {customer_id}: {title} - {message}"}

@router.post("/send-to-customer/{customer_id}")
def send_notification_to_customer(
    customer_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    send_via_email: bool = False,
    send_via_sms: bool = False,
    db: Session = Depends(get_db)
):
    """Send notification to specific customer"""
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        notification = Notification(
            customer_id=customer.id,
            title=title,
            message=message,
            type=notification_type,
            send_via_email=send_via_email,
            send_via_sms=send_via_sms,
            is_sent=True
        )
        db.add(notification)
        db.commit()
        
        return {"message": "Notification sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-to-user/{user_id}")
def send_notification_to_user(
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    send_via_email: bool = False,
    send_via_sms: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Send notification to specific user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        notification = Notification(
            user_id=user.id,
            title=title,
            message=message,
            type=notification_type,
            send_via_email=send_via_email,
            send_via_sms=send_via_sms,
            is_sent=True
        )
        db.add(notification)
        db.commit()
        
        return {"message": "Notification sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted"}

@router.get("/sent")
def get_sent_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get notifications sent to customers and users"""
    notifications = db.query(Notification).filter(
        Notification.is_sent == True
    ).order_by(Notification.created_at.desc()).all()
    
    result = []
    for notif in notifications:
        recipient_name = "All Users & Customers"
        recipient_email = None
        
        if notif.customer_id:
            customer = db.query(Customer).filter(Customer.id == notif.customer_id).first()
            if customer:
                recipient_name = customer.contact_person or customer.email
                recipient_email = customer.email
        elif notif.user_id:
            user = db.query(User).filter(User.id == notif.user_id).first()
            if user:
                recipient_name = f"{user.first_name} {user.last_name}"
                recipient_email = user.email
        
        result.append({
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "type": notif.type,
            "recipient_name": recipient_name,
            "recipient_email": recipient_email,
            "created_at": notif.created_at
        })
    
    return result