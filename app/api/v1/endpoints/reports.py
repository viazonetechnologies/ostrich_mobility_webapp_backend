from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.sales import Sale
from app.models.customer import Customer
from app.models.product import Product
import io
import csv

router = APIRouter()

@router.get("/sales-summary")
def get_sales_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_type: Optional[str] = None,
    region: Optional[str] = None,
    sales_executive_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales summary with filters"""
    query = db.query(Sale).join(Customer, Sale.customer_id == Customer.id).join(User, Sale.created_by == User.id, isouter=True)
    
    # Role-based filtering
    if current_user.role.value == 'sales_executive':
        query = query.filter(Sale.created_by == current_user.id)
    elif current_user.role.value in ['regional_officer', 'manager']:
        query = query.filter((User.region == current_user.region) | (Sale.created_by == None))
    # Admin/Super Admin can filter by region and sales executive
    elif current_user.role.value in ['super_admin', 'admin']:
        if region:
            query = query.filter(User.region == region)
        if sales_executive_id:
            query = query.filter(Sale.created_by == sales_executive_id)
    
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    
    sales = query.all()
    
    # Filter by customer type if specified
    if customer_type:
        sales = [s for s in sales if s.customer.customer_type == customer_type]
    
    total_sales = len(sales)
    total_revenue = sum(float(s.total_amount) for s in sales)
    
    # Group by customer type
    by_customer_type = {}
    for sale in sales:
        ctype = sale.customer.customer_type
        if ctype not in by_customer_type:
            by_customer_type[ctype] = {'count': 0, 'revenue': 0}
        by_customer_type[ctype]['count'] += 1
        by_customer_type[ctype]['revenue'] += float(sale.total_amount)
    
    # Group by payment status
    by_payment_status = {}
    for sale in sales:
        status = sale.payment_status or 'pending'
        if status not in by_payment_status:
            by_payment_status[status] = {'count': 0, 'revenue': 0}
        by_payment_status[status]['count'] += 1
        by_payment_status[status]['revenue'] += float(sale.total_amount)
    
    return {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'by_customer_type': by_customer_type,
        'by_payment_status': by_payment_status,
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'customer_type': customer_type
        }
    }

@router.get("/sales-details")
def get_sales_details(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_type: Optional[str] = None,
    region: Optional[str] = None,
    sales_executive_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed sales list with filters"""
    query = db.query(Sale).join(Customer).join(User, Sale.created_by == User.id, isouter=True)
    
    # Role-based filtering
    if current_user.role.value == 'sales_executive':
        query = query.filter(Sale.created_by == current_user.id)
    elif current_user.role.value in ['regional_officer', 'manager']:
        query = query.filter((User.region == current_user.region) | (Sale.created_by == None))
    # Admin/Super Admin can filter by region and sales executive
    elif current_user.role.value in ['super_admin', 'admin']:
        if region:
            query = query.filter(User.region == region)
        if sales_executive_id:
            query = query.filter(Sale.created_by == sales_executive_id)
    
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)
    
    sales = query.all()
    
    return [{
        'sale_number': sale.sale_number,
        'sale_date': sale.sale_date,
        'customer_name': sale.customer.contact_person,
        'customer_type': sale.customer.customer_type,
        'total_amount': float(sale.total_amount),
        'payment_status': sale.payment_status,
        'delivery_status': sale.delivery_status,
        'created_at': sale.created_at
    } for sale in sales]

@router.get("/export-sales-csv")
def export_sales_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_type: Optional[str] = None,
    region: Optional[str] = None,
    sales_executive_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export sales report as CSV"""
    query = db.query(Sale).join(Customer).join(User, Sale.created_by == User.id, isouter=True)
    
    # Role-based filtering
    if current_user.role.value == 'sales_executive':
        query = query.filter(Sale.created_by == current_user.id)
    elif current_user.role.value in ['regional_officer', 'manager']:
        query = query.filter((User.region == current_user.region) | (Sale.created_by == None))
    # Admin/Super Admin can filter by region and sales executive
    elif current_user.role.value in ['super_admin', 'admin']:
        if region:
            query = query.filter(User.region == region)
        if sales_executive_id:
            query = query.filter(Sale.created_by == sales_executive_id)
    
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)
    
    sales = query.all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Sale Number', 'Sale Date', 'Customer Name', 'Customer Type',
        'Total Amount', 'Payment Status', 'Delivery Status', 'Created At'
    ])
    
    # Write data
    for sale in sales:
        writer.writerow([
            sale.sale_number,
            sale.sale_date,
            sale.customer.contact_person,
            sale.customer.customer_type.upper(),
            float(sale.total_amount),
            sale.payment_status or 'pending',
            sale.delivery_status or 'pending',
            sale.created_at
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=sales_report_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )
