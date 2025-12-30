from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.product import Product, ProductCategory
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductCategoryCreate, ProductCategoryResponse
)

router = APIRouter()

def generate_product_code(db: Session) -> str:
    last_product = db.query(Product).order_by(Product.id.desc()).first()
    if last_product:
        last_number = int(last_product.product_code[3:])
        return f"PRD{last_number + 1:06d}"
    return "PRD000001"

# Product Category endpoints
@router.get("/categories/", response_model=List[ProductCategoryResponse])
def read_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(ProductCategory).offset(skip).limit(limit).all()
    return categories

@router.post("/categories/", response_model=ProductCategoryResponse)
def create_category(
    category: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_category = ProductCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Product endpoints
@router.get("/", response_model=List[ProductResponse])
def read_products(
    skip: int = 0,
    limit: int = 100,
    category_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.sales import SaleItem
    from sqlalchemy import func
    
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    products = query.offset(skip).limit(limit).all()
    
    # Add sales information to each product
    for product in products:
        sales_info = db.query(
            func.count(SaleItem.id).label('total_sales'),
            func.sum(SaleItem.quantity).label('total_quantity')
        ).filter(SaleItem.product_id == product.id).first()
        
        product.total_sales = sales_info.total_sales or 0
        product.total_quantity = sales_info.total_quantity or 0
    
    return products

@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Check if category exists if provided
    if product.category_id:
        category = db.query(ProductCategory).filter(ProductCategory.id == product.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product category not found"
            )
    
    product_code = generate_product_code(db)
    
    db_product = Product(
        product_code=product_code,
        **product.dict()
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=ProductResponse)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.get("/by-customer/{customer_id}", response_model=List[ProductResponse])
def get_products_by_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.sales import Sale, SaleItem
    from sqlalchemy import func
    
    # Get products with total quantity purchased by this customer
    products_with_qty = db.query(
        Product,
        func.sum(SaleItem.quantity).label('purchased_quantity')
    ).join(
        SaleItem, Product.id == SaleItem.product_id
    ).join(
        Sale, SaleItem.sale_id == Sale.id
    ).filter(
        Sale.customer_id == customer_id
    ).group_by(Product.id).all()
    
    # Add purchased quantity to each product
    products = []
    for product, qty in products_with_qty:
        product.purchased_quantity = qty
        products.append(product)
    
    return products

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}