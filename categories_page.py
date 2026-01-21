from flask import jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime
import pymysql
try:
    from database import get_db, sanitize_input
except ImportError:
    # Fallback if database module not available
    def get_db():
        return None
    def sanitize_input(text):
        return str(text).strip() if text else ''

def register_categories_routes(app):
    @app.route('/api/v1/categories/', methods=['GET'])
    @jwt_required()
    def get_categories():
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT id, name, description, is_active, created_at FROM product_categories ORDER BY id ASC")
            categories = cursor.fetchall()
            conn.close()
            return jsonify(categories)
        except Exception as e:
            print(f"Get categories error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/categories/', methods=['POST'])
    @jwt_required()
    def create_category():
        try:
            data = request.get_json()
            if not data or not data.get('name'):
                return jsonify({'error': 'Category name is required'}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Insert category
            query = "INSERT INTO product_categories (name, description, is_active, created_at) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (
                sanitize_input(data.get('name', '')),
                sanitize_input(data.get('description', '')),
                data.get('is_active', True),
                datetime.now()
            ))
            
            category_id = cursor.lastrowid
            conn.commit()
            
            # Get created category
            cursor.execute("SELECT id, name, description, is_active, created_at FROM product_categories WHERE id = %s", (category_id,))
            category = cursor.fetchone()
            
            conn.close()
            return jsonify(category), 201
        except Exception as e:
            print(f"Create category error: {e}")
            return jsonify({'error': 'Failed to create category'}), 500
    
    @app.route('/api/v1/categories/<int:category_id>', methods=['PUT'])
    @jwt_required()
    def update_category(category_id):
        try:
            data = request.get_json()
            print(f"Update category {category_id} with data: {data}")
            
            conn = get_db()
            if not conn:
                print("Database connection failed")
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Simple update with minimal validation
            name = data.get('name', '').strip() if data.get('name') else 'Unnamed Category'
            description = data.get('description', '').strip() if data.get('description') else ''
            is_active = data.get('is_active', True)
            
            query = "UPDATE product_categories SET name = %s, description = %s, is_active = %s WHERE id = %s"
            cursor.execute(query, (name, description, is_active, category_id))
            
            conn.commit()
            print(f"Category {category_id} updated successfully")
            
            # Get updated category
            cursor.execute("SELECT id, name, description, is_active, created_at FROM product_categories WHERE id = %s", (category_id,))
            category = cursor.fetchone()
            
            conn.close()
            return jsonify(category)
        except Exception as e:
            print(f"Update category error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/categories/<int:category_id>', methods=['DELETE'])
    @jwt_required()
    def delete_category(category_id):
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("DELETE FROM product_categories WHERE id = %s", (category_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Category deleted successfully'})
        except Exception as e:
            print(f"Delete category error: {e}")
            return jsonify({'error': 'Failed to delete category'}), 500