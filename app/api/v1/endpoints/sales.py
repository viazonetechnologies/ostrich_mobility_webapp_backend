from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.sales import Sale, SaleItem
from app.models.customer import Customer
from app.models.product import Product
from app.schemas.sales import SaleCreate, SaleResponse
from datetime import datetime, timedelta

router = APIRouter()

def generate_sale_number(db: Session) -> str:
    last_sale = db.query(Sale).order_by(Sale.id.desc()).first()
    if last_sale:
        last_number = int(last_sale.sale_number[3:])
        return f"SAL{last_number + 1:06d}"
    return "SAL000001"

@router.get("/", response_model=List[SaleResponse])
def read_sales(
    skip: int = 0,
    limit: int = 100,
    customer_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import joinedload
    
    query = db.query(Sale).options(
        joinedload(Sale.customer),
        joinedload(Sale.creator),
        joinedload(Sale.items).joinedload(SaleItem.product)
    ).order_by(Sale.id.desc())
    
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)
    
    sales = query.offset(skip).limit(limit).all()
    
    # Build response with product names
    response_sales = []
    for sale in sales:
        sale_dict = {
            "id": sale.id,
            "sale_number": sale.sale_number,
            "customer_id": sale.customer_id,
            "sale_date": sale.sale_date,
            "total_amount": sale.total_amount,
            "discount_percentage": sale.discount_percentage,
            "discount_amount": sale.discount_amount,
            "final_amount": sale.final_amount,
            "payment_status": sale.payment_status,
            "delivery_status": sale.delivery_status,
            "delivery_date": sale.delivery_date,
            "delivery_address": sale.delivery_address,
            "notes": sale.notes,
            "created_at": sale.created_at,
            "updated_at": sale.updated_at,
            "customer_name": sale.customer.contact_person if sale.customer else None,
            "created_by_name": f"{sale.creator.first_name} {sale.creator.last_name}" if sale.creator else None,
            "items": []
        }
        
        for item in sale.items:
            item_dict = {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "serial_number": item.serial_number,
                "warranty_start_date": item.warranty_start_date,
                "warranty_end_date": item.warranty_end_date,
                "is_warranty_active": item.is_warranty_active,
                "product_name": item.product.name if item.product else "Unknown Product"
            }
            sale_dict["items"].append(item_dict)
        
        response_sales.append(sale_dict)
    
    return response_sales

@router.post("/", response_model=SaleResponse)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate required fields
    if not sale.customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID is required"
        )
    
    # Skip items validation if not provided (for simple sale creation)
    # if not sale.items or len(sale.items) == 0:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="At least one sale item is required"
    #     )
    
    if sale.total_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total amount must be greater than 0"
        )
    
    if sale.final_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Final amount must be greater than 0"
        )
    
    # Validate each item (if any)
    if sale.items:
        for item in sale.items:
            if not item.product_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product ID is required for all items"
                )
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be greater than 0"
                )
            if item.unit_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unit price must be greater than 0"
                )
    
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    sale_number = generate_sale_number(db)
    
    # Create sale record
    db_sale = Sale(
        sale_number=sale_number,
        customer_id=sale.customer_id,
        sale_date=sale.sale_date,
        total_amount=sale.total_amount,
        discount_percentage=sale.discount_percentage,
        discount_amount=sale.discount_amount,
        final_amount=sale.final_amount,
        payment_status=sale.payment_status if hasattr(sale, 'payment_status') else 'pending',
        delivery_status=sale.delivery_status if hasattr(sale, 'delivery_status') else 'pending',
        delivery_date=sale.delivery_date if hasattr(sale, 'delivery_date') else None,
        delivery_address=sale.delivery_address,
        notes=sale.notes,
        created_by=current_user.id
    )
    
    db.add(db_sale)
    db.flush()  # Get the sale ID
    
    # Create sale items (if any)
    if sale.items:
        for item in sale.items:
            # Verify product exists
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item.product_id} not found"
                )
            
            # Calculate warranty dates
            warranty_start = datetime.now()
            warranty_end = warranty_start + timedelta(days=product.warranty_period * 30)
            
            db_item = SaleItem(
                sale_id=db_sale.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.quantity * item.unit_price,
                serial_number=item.serial_number,
                warranty_start_date=warranty_start,
                warranty_end_date=warranty_end
            )
            
            db.add(db_item)
    
    db.commit()
    db.refresh(db_sale)
    
    # Load relationships and build response with product names
    from sqlalchemy.orm import joinedload
    sale_with_relations = db.query(Sale).options(
        joinedload(Sale.customer),
        joinedload(Sale.creator),
        joinedload(Sale.items).joinedload(SaleItem.product)
    ).filter(Sale.id == db_sale.id).first()
    
    # Build response with product names
    sale_dict = {
        "id": sale_with_relations.id,
        "sale_number": sale_with_relations.sale_number,
        "customer_id": sale_with_relations.customer_id,
        "sale_date": sale_with_relations.sale_date,
        "total_amount": sale_with_relations.total_amount,
        "discount_percentage": sale_with_relations.discount_percentage,
        "discount_amount": sale_with_relations.discount_amount,
        "final_amount": sale_with_relations.final_amount,
        "payment_status": sale_with_relations.payment_status,
        "delivery_status": sale_with_relations.delivery_status,
        "delivery_date": sale_with_relations.delivery_date,
        "delivery_address": sale_with_relations.delivery_address,
        "notes": sale_with_relations.notes,
        "created_at": sale_with_relations.created_at,
        "updated_at": sale_with_relations.updated_at,
        "customer_name": sale_with_relations.customer.contact_person if sale_with_relations.customer else None,
        "created_by_name": f"{sale_with_relations.creator.first_name} {sale_with_relations.creator.last_name}" if sale_with_relations.creator else None,
        "items": []
    }
    
    for item in sale_with_relations.items:
        item_dict = {
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "serial_number": item.serial_number,
            "warranty_start_date": item.warranty_start_date,
            "warranty_end_date": item.warranty_end_date,
            "is_warranty_active": item.is_warranty_active,
            "product_name": item.product.name if item.product else "Unknown Product"
        }
        sale_dict["items"].append(item_dict)
    
    return sale_dict

@router.get("/{sale_id}", response_model=SaleResponse)
def read_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import joinedload
    
    sale = db.query(Sale).options(
        joinedload(Sale.customer),
        joinedload(Sale.creator),
        joinedload(Sale.items).joinedload(SaleItem.product)
    ).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    # Build response with product names
    sale_dict = {
        "id": sale.id,
        "sale_number": sale.sale_number,
        "customer_id": sale.customer_id,
        "sale_date": sale.sale_date,
        "total_amount": sale.total_amount,
        "discount_percentage": sale.discount_percentage,
        "discount_amount": sale.discount_amount,
        "final_amount": sale.final_amount,
        "payment_status": sale.payment_status,
        "delivery_status": sale.delivery_status,
        "delivery_date": sale.delivery_date,
        "delivery_address": sale.delivery_address,
        "notes": sale.notes,
        "created_at": sale.created_at,
        "updated_at": sale.updated_at,
        "customer_name": sale.customer.contact_person if sale.customer else None,
        "created_by_name": f"{sale.creator.first_name} {sale.creator.last_name}" if sale.creator else None,
        "items": []
    }
    
    for item in sale.items:
        item_dict = {
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "serial_number": item.serial_number,
            "warranty_start_date": item.warranty_start_date,
            "warranty_end_date": item.warranty_end_date,
            "is_warranty_active": item.is_warranty_active,
            "product_name": item.product.name if item.product else "Unknown Product"
        }
        sale_dict["items"].append(item_dict)
    
    return sale_dict

@router.put("/{sale_id}", response_model=SaleResponse)
def update_sale(
    sale_id: int,
    sale_update: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    # Update sale fields
    sale.customer_id = sale_update.customer_id
    sale.sale_date = sale_update.sale_date
    sale.total_amount = sale_update.total_amount
    sale.discount_percentage = sale_update.discount_percentage
    sale.discount_amount = sale_update.discount_amount
    sale.final_amount = sale_update.final_amount
    sale.payment_status = sale_update.payment_status if hasattr(sale_update, 'payment_status') else sale.payment_status
    sale.delivery_status = sale_update.delivery_status if hasattr(sale_update, 'delivery_status') else sale.delivery_status
    sale.delivery_date = sale_update.delivery_date if hasattr(sale_update, 'delivery_date') else sale.delivery_date
    sale.delivery_address = sale_update.delivery_address
    sale.notes = sale_update.notes
    
    # Delete existing items and create new ones
    db.query(SaleItem).filter(SaleItem.sale_id == sale_id).delete()
    
    # Create new sale items
    for item in sale_update.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item.product_id} not found"
            )
        
        warranty_start = datetime.now()
        warranty_end = warranty_start + timedelta(days=product.warranty_period * 30)
        
        db_item = SaleItem(
            sale_id=sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price,
            serial_number=item.serial_number,
            warranty_start_date=warranty_start,
            warranty_end_date=warranty_end
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(sale)
    
    # Load relationships and build response with product names
    from sqlalchemy.orm import joinedload
    sale_with_relations = db.query(Sale).options(
        joinedload(Sale.customer),
        joinedload(Sale.creator),
        joinedload(Sale.items).joinedload(SaleItem.product)
    ).filter(Sale.id == sale.id).first()
    
    # Build response with product names
    sale_dict = {
        "id": sale_with_relations.id,
        "sale_number": sale_with_relations.sale_number,
        "customer_id": sale_with_relations.customer_id,
        "sale_date": sale_with_relations.sale_date,
        "total_amount": sale_with_relations.total_amount,
        "discount_percentage": sale_with_relations.discount_percentage,
        "discount_amount": sale_with_relations.discount_amount,
        "final_amount": sale_with_relations.final_amount,
        "payment_status": sale_with_relations.payment_status,
        "delivery_status": sale_with_relations.delivery_status,
        "delivery_date": sale_with_relations.delivery_date,
        "delivery_address": sale_with_relations.delivery_address,
        "notes": sale_with_relations.notes,
        "created_at": sale_with_relations.created_at,
        "updated_at": sale_with_relations.updated_at,
        "customer_name": sale_with_relations.customer.contact_person if sale_with_relations.customer else None,
        "created_by_name": f"{sale_with_relations.creator.first_name} {sale_with_relations.creator.last_name}" if sale_with_relations.creator else None,
        "items": []
    }
    
    for item in sale_with_relations.items:
        item_dict = {
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "serial_number": item.serial_number,
            "warranty_start_date": item.warranty_start_date,
            "warranty_end_date": item.warranty_end_date,
            "is_warranty_active": item.is_warranty_active,
            "product_name": item.product.name if item.product else "Unknown Product"
        }
        sale_dict["items"].append(item_dict)
    
    return sale_dict

@router.delete("/{sale_id}")
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    db.delete(sale)
    db.commit()
    return {"message": "Sale deleted successfully"}