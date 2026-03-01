from flask import jsonify, request
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql
from datetime import datetime

try:
    import pandas as pd
    import openpyxl
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

def register_service_tickets_routes(app):
    """Register service tickets routes"""
    
    @app.route('/api/v1/service-tickets/', methods=['GET'])
    @jwt_required(optional=True)
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
            
            cursor.execute("SELECT MAX(id) as max_id FROM service_tickets")
            result = cursor.fetchone()
            next_id = (result[0] or 0) + 1
            ticket_number = f"TKT{next_id:06d}"
            
            cursor.execute("""
                INSERT INTO service_tickets 
                (ticket_number, customer_id, product_id, issue_description, priority, status, 
                assigned_staff_id, warranty_status, resolution_details, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ticket_number,
                data.get('customer_id'),
                data.get('product_id'),
                data.get('issue_description'),
                data.get('priority', 'MEDIUM'),
                data.get('status', 'OPEN'),
                data.get('assigned_staff_id'),
                data.get('warranty_status', 'No'),
                data.get('resolution_details'),
                data.get('remarks')
            ))
            
            conn.commit()
            conn.close()
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
                    status=%s, assigned_staff_id=%s, warranty_status=%s, resolution_details=%s, remarks=%s
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
                data.get('remarks'),
                ticket_id
            ))
            
            conn.commit()
            conn.close()
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
            return jsonify({'message': 'Service ticket deleted'})
            
        except Exception as e:
            print(f"Delete service ticket error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/service-tickets/import', methods=['POST'])
    @jwt_required(optional=True)
    def import_service_tickets():
        """Import service tickets from Excel"""
        if not PANDAS_AVAILABLE:
            return jsonify({'error': 'Excel import requires pandas and openpyxl'}), 503
        
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            df = pd.read_excel(file, engine='openpyxl')
            
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            imported = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    cursor.execute("SELECT id FROM customers WHERE contact_person=%s OR phone=%s LIMIT 1", 
                                 (row.get('Customer Name'), row.get('Contact Number')))
                    customer = cursor.fetchone()
                    if not customer:
                        errors.append(f"Row {idx+2}: Customer not found")
                        continue
                    
                    product_id = None
                    if pd.notna(row.get('Product Model')):
                        cursor.execute("SELECT id FROM products WHERE name=%s LIMIT 1", (row.get('Product Model'),))
                        product = cursor.fetchone()
                        if product:
                            product_id = product['id']
                    
                    engineer_id = None
                    if pd.notna(row.get('Service Engineer Assigned')):
                        names = str(row.get('Service Engineer Assigned')).split()
                        if len(names) >= 2:
                            cursor.execute("SELECT id FROM users WHERE first_name=%s AND last_name=%s LIMIT 1", 
                                         (names[0], names[-1]))
                            engineer = cursor.fetchone()
                            if engineer:
                                engineer_id = engineer['id']
                    
                    cursor.execute("SELECT MAX(id) as max_id FROM service_tickets")
                    result = cursor.fetchone()
                    next_id = (result['max_id'] or 0) + 1
                    ticket_number = f"TKT{next_id:06d}"
                    
                    priority_map = {'Low': 'LOW', 'Medium': 'MEDIUM', 'High': 'HIGH', 'Critical': 'CRITICAL'}
                    priority = priority_map.get(row.get('Priority'), 'MEDIUM')
                    
                    status_map = {'Open': 'OPEN', 'In Progress': 'IN_PROGRESS', 'Completed': 'RESOLVED', 'Closed': 'CLOSED'}
                    status = status_map.get(row.get('Status'), 'OPEN')
                    
                    cursor.execute("""
                        INSERT INTO service_tickets 
                        (ticket_number, customer_id, product_id, issue_description, priority, status, 
                        assigned_staff_id, warranty_status, resolution_details, remarks, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ticket_number,
                        customer['id'],
                        product_id,
                        row.get('Issue Reported', ''),
                        priority,
                        status,
                        engineer_id,
                        row.get('Warranty Status', 'No'),
                        row.get('Resolution Details', ''),
                        row.get('Remarks', ''),
                        pd.to_datetime(row.get('Issue Reported Date')) if pd.notna(row.get('Issue Reported Date')) else datetime.now()
                    ))
                    imported += 1
                except Exception as e:
                    errors.append(f"Row {idx+2}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'message': f'Imported {imported} tickets',
                'imported': imported,
                'errors': errors
            })
            
        except Exception as e:
            print(f"Import error: {e}")
            return jsonify({'error': str(e)}), 500
