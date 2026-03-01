from flask import jsonify, request
from flask_jwt_extended import jwt_required
from database import get_db
from cache_config import cache_response, clear_cache_pattern
import pymysql

def register_service_tickets_routes(app):
    """Register service tickets routes"""
    
    @app.route('/api/v1/service-tickets/', methods=['GET'])
    @jwt_required(optional=True)
    @cache_response(timeout=30)
    def get_service_tickets():
        """Get all service tickets with customer and product details"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT 
                    st.*,
                    c.contact_person as customer_name,
                    c.phone as customer_phone,
                    c.email as customer_email,
                    c.city as customer_city,
                    c.state as customer_state,
                    p.name as product_name,
                    pc.name as product_category,
                    u.first_name as engineer_first_name,
                    u.last_name as engineer_last_name
                FROM service_tickets st
                LEFT JOIN customers c ON st.customer_id = c.id
                LEFT JOIN products p ON st.product_id = p.id
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                LEFT JOIN users u ON st.assigned_staff_id = u.id
                ORDER BY st.id DESC
            """)
            tickets = cursor.fetchall()
            conn.close()
            return jsonify(tickets)
            
        except Exception as e:
            print(f"Get service tickets error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/service-tickets/', methods=['POST'])
    @jwt_required(optional=True)
    def create_service_ticket():
        """Create new service ticket"""
        try:
            data = request.get_json()
            conn = get_db()
            cursor = conn.cursor()
            
            # Generate ticket number
            cursor.execute("SELECT MAX(id) as max_id FROM service_tickets")
            result = cursor.fetchone()
            next_id = (result[0] or 0) + 1
            ticket_number = f"TKT{next_id:06d}"
            
            cursor.execute("""
                INSERT INTO service_tickets 
                (ticket_number, customer_id, product_id, issue_description, priority, status, 
                assigned_staff_id, warranty_status, resolution_details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ticket_number,
                data.get('customer_id'),
                data.get('product_id'),
                data.get('issue_description'),
                data.get('priority', 'MEDIUM'),
                data.get('status', 'OPEN'),
                data.get('assigned_staff_id'),
                data.get('warranty_status', 'No'),
                data.get('resolution_details')
            ))
            
            conn.commit()
            conn.close()
            clear_cache_pattern('/api/v1/service-tickets/')
            return jsonify({'message': 'Service ticket created', 'ticket_number': ticket_number})
            
        except Exception as e:
            print(f"Create service ticket error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/service-tickets/<int:ticket_id>', methods=['PUT'])
    @jwt_required(optional=True)
    def update_service_ticket(ticket_id):
        """Update service ticket"""
        try:
            data = request.get_json()
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE service_tickets 
                SET customer_id=%s, product_id=%s, issue_description=%s, priority=%s, 
                    status=%s, assigned_staff_id=%s, warranty_status=%s, resolution_details=%s
                WHERE id=%s
            """, (
                data.get('customer_id'),
                data.get('product_id'),
                data.get('issue_description'),
                data.get('priority'),
                data.get('status'),
                data.get('assigned_staff_id'),
                data.get('warranty_status'),
                data.get('resolution_details'),
                ticket_id
            ))
            
            conn.commit()
            conn.close()
            clear_cache_pattern('/api/v1/service-tickets/')
            return jsonify({'message': 'Service ticket updated'})
            
        except Exception as e:
            print(f"Update service ticket error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/service-tickets/<int:ticket_id>', methods=['DELETE'])
    @jwt_required(optional=True)
    def delete_service_ticket(ticket_id):
        """Delete service ticket"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM service_tickets WHERE id=%s", (ticket_id,))
            conn.commit()
            conn.close()
            clear_cache_pattern('/api/v1/service-tickets/')
            return jsonify({'message': 'Service ticket deleted'})
            
        except Exception as e:
            print(f"Delete service ticket error: {e}")
            return jsonify({'error': str(e)}), 500
