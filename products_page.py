from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import pymysql
import re
from database import get_db, sanitize_input
from cloud_image_service import hostinger_image_service

def check_permission(user_role, required_role):
    """Check user permissions"""
    roles = {'super_admin': 5, 'admin': 4, 'regional_officer': 3, 'manager': 2, 'sales_executive': 1}
    return roles.get(user_role, 0) >= roles.get(required_role, 0)

def validate_product_data(data):
    """Validate product data"""
    errors = []
    
    if not data.get('name', '').strip():
        errors.append('Product name is required')
    
    if not data.get('description', '').strip():
        errors.append('Description is required')
    
    if not data.get('category_id'):
        errors.append('Category is required')
    
    # Validate product code format
    sku = data.get('sku', '').strip()
    if sku and not re.match(r'^PROD\d{5}$', sku):
        errors.append('Product code must be in format PROD00001 (PROD followed by 5 digits)')
    
    price = data.get('price')
    if not price or float(price) <= 0:
        errors.append('Price must be greater than 0')
    
    # Validate offer price if provided
    offer_price = data.get('offer_price')
    if offer_price:
        try:
            offer_price_float = float(offer_price)
            price_float = float(price) if price else 0
            
            if offer_price_float <= 0:
                errors.append('Offer price must be greater than 0')
            elif offer_price_float >= price_float:
                errors.append('Offer price must be less than regular price')
        except (ValueError, TypeError):
            errors.append('Offer price must be a valid number')
    
    # Validate trending position if trending is enabled
    if data.get('is_trending') and data.get('trending_position'):
        try:
            pos = int(data.get('trending_position'))
            if pos < 1 or pos > 100:
                errors.append('Trending position must be between 1 and 100')
        except (ValueError, TypeError):
            errors.append('Trending position must be a valid number')
    
    return errors

def register_products_routes(app):
    """Register product page routes"""
    
    @app.route('/api/v1/products/categories/', methods=['GET'])
    @jwt_required()
    def get_product_categories():
        """Get all categories"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT id, name FROM product_categories WHERE is_active = 1 ORDER BY name")
            categories = cursor.fetchall()
            
            conn.close()
            return jsonify(categories)
            
        except Exception as e:
            print(f"Get categories error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/products/', methods=['GET'])
    @jwt_required()
    def get_products():
        """Get all products"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get sort parameters
            sort_order = request.args.get('sort_order', 'asc')
            
            # Validate sort order
            if sort_order not in ['asc', 'desc']:
                sort_order = 'asc'
            
            # Query using actual database structure
            query = f"""
                SELECT p.id, p.name, 
                       COALESCE(p.product_code, '') as sku, 
                       COALESCE(p.description, '') as description, 
                       COALESCE(p.price, 0) as price, 
                       COALESCE(p.offer_price, NULL) as offer_price,
                       COALESCE(p.stock_quantity, 0) as stock_quantity,
                       COALESCE(p.stock_status, 'in_stock') as stock_status,
                       COALESCE(p.image_url, '') as image_url, 
                       COALESCE(p.is_trending, 0) as is_trending,
                       COALESCE(p.trending_position, NULL) as trending_position,
                       COALESCE(p.is_active, 1) as is_active,
                       p.category_id, 
                       COALESCE(c.name, 'No Category') as category_name,
                       p.created_at
                FROM products p
                LEFT JOIN product_categories c ON p.category_id = c.id
                ORDER BY p.product_code {sort_order.upper()}
            """
            
            cursor.execute(query)
            products = cursor.fetchall()
            
            conn.close()
            return jsonify(products)
            
        except Exception as e:
            print(f"Get products error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/products/', methods=['POST'])
    @jwt_required()
    def create_product():
        """Create new product"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate data
            validation_errors = validate_product_data(data)
            if validation_errors:
                return jsonify({'error': validation_errors[0]}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Insert using actual column names including trending fields
            query = """
                INSERT INTO products (name, product_code, description, price, offer_price, 
                                    stock_quantity, image_url, category_id, is_trending, 
                                    trending_position, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                data.get('name', ''),
                data.get('sku', ''),
                data.get('description', ''),
                data.get('price', 0),
                data.get('offer_price'),
                data.get('stock_quantity', 0),
                data.get('image_url', ''),
                data.get('category_id'),
                data.get('is_trending', False),
                data.get('trending_position') if data.get('is_trending') else None,
                data.get('is_active', True),

                datetime.now()
            ))
            
            product_id = cursor.lastrowid
            conn.commit()
            
            # Get created product
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            
            conn.close()
            return jsonify(product), 201
            
        except Exception as e:
            print(f"Create product error: {e}")
            return jsonify({'error': 'Failed to create product'}), 500
    
    @app.route('/api/v1/products/<int:product_id>', methods=['PUT'])
    @jwt_required()
    def update_product(product_id):
        """Update existing product"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Update product
            query = """
                UPDATE products SET 
                    name = %s, product_code = %s, description = %s, 
                    price = %s, offer_price = %s, stock_quantity = %s, 
                    image_url = %s, category_id = %s, is_trending = %s, 
                    trending_position = %s, is_active = %s
                WHERE id = %s
            """
            cursor.execute(query, (
                sanitize_input(data.get('name', '')),
                sanitize_input(data.get('sku', '')),
                sanitize_input(data.get('description', '')),
                data.get('price', 0),
                data.get('offer_price'),
                data.get('stock_quantity', 0),
                data.get('image_url', ''),
                data.get('category_id'),
                data.get('is_trending', False),
                data.get('trending_position') if data.get('is_trending') else None,
                data.get('is_active', True),
                product_id
            ))
            
            conn.commit()
            
            # Get updated product
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            
            conn.close()
            return jsonify(product)
            
        except Exception as e:
            print(f"Update product error: {e}")
            return jsonify({'error': 'Failed to update product'}), 500
    
    @app.route('/api/v1/products/<int:product_id>', methods=['DELETE'])
    @jwt_required()
    def delete_product(product_id):
        """Delete product"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if product exists
            cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Product not found'}), 404
            
            # Delete product
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Product deleted successfully'})
            
        except Exception as e:
            print(f"Delete product error: {e}")
            return jsonify({'error': 'Failed to delete product'}), 500
    
    @app.route('/api/v1/products/upload-image', methods=['POST'])
    @jwt_required()
    def upload_product_image():
        """Upload product image to cloud storage"""
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if file_ext not in allowed_extensions:
                return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG, GIF, WEBP allowed'}), 400
            
            # Upload to cloud storage
            image_url = hostinger_image_service.upload_image(file, 'products')
            
            if image_url:
                return jsonify({'image_url': image_url}), 200
            else:
                return jsonify({'error': 'Failed to upload image'}), 500
                
        except Exception as e:
            print(f"Upload image error: {e}")
            return jsonify({'error': 'Failed to upload image'}), 500
    
    @app.route('/api/v1/products/<int:product_id>/image', methods=['PUT'])
    @jwt_required()
    def update_product_image_url(product_id):
        """Update product image URL"""
        try:
            data = request.get_json()
            image_url = data.get('image_url', '')
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if product exists
            cursor.execute("SELECT id, image_url FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            if not product:
                conn.close()
                return jsonify({'error': 'Product not found'}), 404
            
            # Delete old image if exists
            old_image_url = product.get('image_url')
            if old_image_url and old_image_url != image_url:
                hostinger_image_service.delete_image(old_image_url)
            
            # Update image URL
            cursor.execute(
                "UPDATE products SET image_url = %s WHERE id = %s",
                (image_url, product_id)
            )
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Image updated successfully', 'image_url': image_url})
            
        except Exception as e:
            print(f"Update image error: {e}")
            return jsonify({'error': 'Failed to update image'}), 500
