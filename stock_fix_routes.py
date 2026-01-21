from flask import request, jsonify
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql

def register_stock_fix_routes(app):
    """Register stock fix routes"""
    
    @app.route('/api/v1/products/fix-stock', methods=['POST'])
    @jwt_required()
    def fix_product_stock():
        """Fix product stock quantities"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Update all products with random stock quantities
            stock_updates = [
                (50, 1),   # 3HP Motor - 50 units
                (25, 2),   # 5HP Motor - 25 units  
                (100, 3),  # MCB - 100 units
                (15, 4),   # MCCB - 15 units
                (8, 5),    # Panel - 8 units (low stock)
                (200, 6),  # Cable - 200 units
                (5, 7),    # 10HP Motor - 5 units (low stock)
                (75, 8)    # Contactor - 75 units
            ]
            
            for stock_qty, product_id in stock_updates:
                cursor.execute(
                    "UPDATE products SET stock_quantity = %s WHERE id = %s",
                    (stock_qty, product_id)
                )
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Stock quantities updated successfully'})
            
        except Exception as e:
            print(f"Fix stock error: {e}")
            return jsonify({'error': 'Failed to fix stock'}), 500