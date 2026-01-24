from flask import jsonify, request
from flask_jwt_extended import jwt_required
from database import get_db
from datetime import datetime
import pymysql

def register_service_tickets_routes(app):
    """Register service tickets routes"""
    
    @app.route('/api/v1/service-tickets/', methods=['GET', 'POST'])
    @jwt_required()
    def handle_service_tickets():
        """Get all service tickets or create new one"""
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("SELECT * FROM service_tickets ORDER BY created_at DESC")
                tickets = cursor.fetchall()
                
                conn.close()
                return jsonify(tickets)
                
            except Exception as e:
                print(f"Get service tickets error: {e}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Generate service ticket code
                cursor.execute("SELECT MAX(CAST(SUBSTRING(ticket_code, 4) AS UNSIGNED)) as max_num FROM service_tickets WHERE ticket_code LIKE 'SRV%'")
                result = cursor.fetchone()
                next_num = (result['max_num'] or 0) + 1 if result else 1
                ticket_code = f"SRV{next_num:08d}"
                
                # Insert service ticket with generated code
                query = """
                    INSERT INTO service_tickets (ticket_code, customer_id, product_id, issue_description, 
                                               status, priority, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    ticket_code,
                    data.get('customer_id'),
                    data.get('product_id'),
                    data.get('issue_description', ''),
                    data.get('status', 'open'),
                    data.get('priority', 'medium'),
                    datetime.now()
                ))
                
                ticket_id = cursor.lastrowid
                conn.commit()
                
                # Get created ticket
                cursor.execute("SELECT * FROM service_tickets WHERE id = %s", (ticket_id,))
                ticket = cursor.fetchone()
                
                conn.close()
                return jsonify(ticket), 201
                
            except Exception as e:
                print(f"Create service ticket error: {e}")
                return jsonify({'error': 'Failed to create service ticket'}), 500
