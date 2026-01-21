from flask import jsonify
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql

def register_service_tickets_routes(app):
    """Register service tickets routes"""
    
    @app.route('/api/v1/service-tickets/', methods=['GET'])
    @jwt_required()
    def get_service_tickets():
        """Get all service tickets"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM service_tickets ORDER BY created_at DESC LIMIT 10")
            tickets = cursor.fetchall()
            
            conn.close()
            return jsonify(tickets)
            
        except Exception as e:
            print(f"Get service tickets error: {e}")
            return jsonify([])