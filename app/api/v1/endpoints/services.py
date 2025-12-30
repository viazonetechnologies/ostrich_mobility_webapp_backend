from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.service import ServiceTicket
from app.models.customer import Customer
from app.models.notification import Notification
from app.schemas.service import ServiceTicketCreate, ServiceTicketUpdate, ServiceTicketResponse

router = APIRouter()

def generate_ticket_number(db: Session) -> str:
    last_ticket = db.query(ServiceTicket).order_by(ServiceTicket.id.desc()).first()
    if last_ticket:
        last_number = int(last_ticket.ticket_number[3:])
        return f"TKT{last_number + 1:06d}"
    return "TKT000001"

@router.get("/", response_model=List[ServiceTicketResponse])
def read_service_tickets(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    priority_filter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ServiceTicket)
    
    if status_filter:
        query = query.filter(ServiceTicket.status == status_filter)
    
    if priority_filter:
        query = query.filter(ServiceTicket.priority == priority_filter)
    
    # Filter by user role
    if current_user.role.value == "service_staff":
        query = query.filter(ServiceTicket.assigned_staff_id == current_user.id)
    
    tickets = query.offset(skip).limit(limit).all()
    
    for ticket in tickets:
        if ticket.customer:
            ticket.customer_name = ticket.customer.contact_person
        if ticket.assigned_staff:
            ticket.assigned_staff_name = f"{ticket.assigned_staff.first_name} {ticket.assigned_staff.last_name}"
    
    return tickets

@router.post("/", response_model=ServiceTicketResponse)
def create_service_ticket(
    ticket: ServiceTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate required fields
    if not ticket.customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID is required"
        )
    
    if not ticket.issue_description or len(ticket.issue_description.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Issue description must be at least 10 characters"
        )
    
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == ticket.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    ticket_number = generate_ticket_number(db)
    
    db_ticket = ServiceTicket(
        ticket_number=ticket_number,
        **ticket.dict()
    )
    
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    # Create notification for all users
    all_users = db.query(User).all()
    for user in all_users:
        notification = Notification(
            user_id=user.id,
            title="New Service Ticket",
            message=f"New service ticket {ticket_number} from {customer.contact_person}. Priority: {ticket.priority}. Issue: {ticket.issue_description[:50]}...",
            type="warning" if ticket.priority == 'high' else "info"
        )
        db.add(notification)
    db.commit()
    
    return db_ticket

@router.get("/{ticket_id}", response_model=ServiceTicketResponse)
def read_service_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service ticket not found"
        )
    
    if ticket.customer:
        ticket.customer_name = ticket.customer.contact_person
    if ticket.assigned_staff:
        ticket.assigned_staff_name = f"{ticket.assigned_staff.first_name} {ticket.assigned_staff.last_name}"
    
    return ticket

@router.put("/{ticket_id}", response_model=ServiceTicketResponse)
def update_service_ticket(
    ticket_id: int,
    ticket_update: ServiceTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service ticket not found"
        )
    
    update_data = ticket_update.dict(exclude_unset=True)
    old_status = ticket.status
    
    for field, value in update_data.items():
        setattr(ticket, field, value)
    
    db.commit()
    db.refresh(ticket)
    
    # Notify all users if status changed
    if 'status' in update_data and old_status != ticket.status:
        all_users = db.query(User).all()
        for user in all_users:
            notification = Notification(
                user_id=user.id,
                title="Service Ticket Updated",
                message=f"Service ticket {ticket.ticket_number} status changed from {old_status} to {ticket.status}",
                type="success" if ticket.status == 'resolved' else "info"
            )
            db.add(notification)
        db.commit()
    
    return ticket

@router.delete("/{ticket_id}")
def delete_service_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service ticket not found"
        )
    
    db.delete(ticket)
    db.commit()
    return {"message": "Service ticket deleted successfully"}