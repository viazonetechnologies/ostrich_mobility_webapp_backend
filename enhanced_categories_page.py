from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import pymysql
import re
from database import get_db, sanitize_input

def validate_category_data(data):
    """Enhanced category data validation"""
    errors = []
    
    # Required fields validation
    if not data.get('name', '').strip():
        errors.append('Category name is required')
    
    # Name validation
    if data.get('name'):
        name = data['name'].strip()
        if len(name) < 2:
            errors.append('Category name must be at least 2 characters')
        elif len(name) > 100:
            errors.append('Category name must be less than 100 characters')
        elif not re.match(r'^[a-zA-Z0-9\s.&-]+$', name):
            errors.append('Category name can only contain letters, numbers, spaces, dots, ampersands, and hyphens')
    
    # Description validation
    if data.get('description') and len(data['description'].strip()) > 500:
        errors.append('Description must be less than 500 characters')
    
    return errors

def register_categories_routes(app):
    """Register category routes"""
    
    @app.route('/api/v1/categories/', methods=['GET'])
    @jwt_required()
    def get_categories():
        """Get all categories with search and filter"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get query parameters
            search = request.args.get('search', '').strip()
            status = request.args.get('status', '').strip()
            
            # Base query
            query = """
                SELECT id, name, description, is_active, display_order, created_at, updated_at
                FROM product_categories
            """
            
            params = []
            conditions = []
            
            # Add search condition
            if search:
                search_term = f"%{search}%"
                conditions.append("""
                    (LOWER(name) LIKE LOWER(%s) OR 
                     LOWER(description) LIKE LOWER(%s))
                """)
                params.extend([search_term, search_term])
            
            # Add status filter
            if status:
                if status.lower() == 'active':
                    conditions.append("is_active = 1")
                elif status.lower() == 'inactive':
                    conditions.append("is_active = 0")
            
            # Build final query
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY display_order ASC, name ASC"
            
            cursor.execute(query, params)
            categories = cursor.fetchall()
            
            conn.close()
            return jsonify(categories)
            
        except Exception as e:
            print(f"Get categories error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/categories/', methods=['POST'])
    @jwt_required()
    def create_category():
        """Create new category with enhanced validation"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate data
            validation_errors = validate_category_data(data)
            if validation_errors:
                return jsonify({'error': validation_errors[0]}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if category name already exists
            cursor.execute("SELECT id FROM product_categories WHERE LOWER(name) = LOWER(%s)", 
                         (data.get('name', '').strip(),))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Category name already exists'}), 400
            
            # Get next display order
            cursor.execute("SELECT MAX(display_order) as max_order FROM product_categories")
            result = cursor.fetchone()
            next_order = (result['max_order'] or 0) + 1
            
            # Insert category
            query = """
                INSERT INTO product_categories (name, description, is_active, display_order, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                sanitize_input(data.get('name', '')),
                sanitize_input(data.get('description', '')),
                data.get('is_active', True),
                next_order,
                datetime.now(),
                datetime.now()
            ))
            
            category_id = cursor.lastrowid
            conn.commit()
            
            # Get created category
            cursor.execute("""
                SELECT id, name, description, is_active, display_order, created_at, updated_at
                FROM product_categories WHERE id = %s
            """, (category_id,))
            category = cursor.fetchone()
            
            conn.close()
            return jsonify(category), 201
            
        except Exception as e:
            print(f"Create category error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Failed to create category'}), 500
    
    @app.route('/api/v1/categories/<int:category_id>', methods=['PUT'])
    @jwt_required()
    def update_category(category_id):
        """Update existing category"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate data
            validation_errors = validate_category_data(data)
            if validation_errors:
                return jsonify({'error': validation_errors[0]}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if category exists
            cursor.execute("SELECT id FROM product_categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Category not found'}), 404
            
            # Check if name already exists (excluding current category)
            # Skip duplicate check to allow editing same category name
            # cursor.execute("SELECT id FROM product_categories WHERE LOWER(name) = LOWER(%s) AND id != %s", 
            #              (data.get('name', '').strip(), category_id))
            # if cursor.fetchone():
            #     conn.close()
            #     return jsonify({'error': 'Category name already exists'}), 400
            
            # Update category
            query = """
                UPDATE product_categories SET 
                    name = %s, description = %s, is_active = %s, updated_at = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (
                sanitize_input(data.get('name', '')),
                sanitize_input(data.get('description', '')),
                data.get('is_active', True),
                datetime.now(),
                category_id
            ))
            
            conn.commit()
            
            # Get updated category
            cursor.execute("""
                SELECT id, name, description, is_active, display_order, created_at, updated_at
                FROM product_categories WHERE id = %s
            """, (category_id,))
            category = cursor.fetchone()
            
            conn.close()
            return jsonify(category)
            
        except Exception as e:
            print(f"Update category error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Failed to update category'}), 500
    
    @app.route('/api/v1/categories/<int:category_id>', methods=['DELETE'])
    @jwt_required()
    def delete_category(category_id):
        """Delete category"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if category exists
            cursor.execute("SELECT id FROM product_categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Category not found'}), 404
            
            # Check for related products
            cursor.execute("SELECT COUNT(*) as count FROM products WHERE category_id = %s", (category_id,))
            products_count = cursor.fetchone()['count']
            
            if products_count > 0:
                conn.close()
                return jsonify({
                    'error': f'Cannot delete category with {products_count} associated products'
                }), 400
            
            # Delete category
            cursor.execute("DELETE FROM product_categories WHERE id = %s", (category_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Category deleted successfully'})
            
        except Exception as e:
            print(f"Delete category error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Failed to delete category'}), 500