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
            if not file.filename:
                return jsonify({'error': 'No file selected'}), 400
                
            print(f"Processing file: {file.filename}")
            df = pd.read_excel(file, engine='openpyxl')
            print(f"Excel loaded: {len(df)} rows, columns: {list(df.columns)}")
            
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            imported = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    cust_name = str(row.get('Customer Name', '')).strip()
                    cust_phone = str(row.get('Contact Number', '')).replace(' ', '').strip()
                    cust_email = str(row.get('Customer Email ID', '')).strip() if pd.notna(row.get('Customer Email ID')) else ''
                    cust_city = str(row.get('Customer Location-CITY', '')).strip() if pd.notna(row.get('Customer Location-CITY')) else ''
                    cust_state = str(row.get('Customer Location - STATE', '')).strip() if pd.notna(row.get('Customer Location - STATE')) else ''
                    issue_desc = str(row.get('Issue Reported', '')).strip()
                    
                    if not cust_name:
                        errors.append(f"Row {idx+2}: Missing customer name")
                        continue
                    
                    cursor.execute("SELECT id FROM customers WHERE contact_person=%s OR (phone=%s AND phone!='') LIMIT 1", 
                                 (cust_name, cust_phone))
                    customer = cursor.fetchone()
                    
                    if not customer and cust_phone:
                        cursor.execute("SELECT id FROM customers WHERE phone LIKE %s LIMIT 1", (f"%{cust_phone[-10:]}%",))
                        customer = cursor.fetchone()
                    
                    if not customer:
                        cursor.execute("SELECT MAX(id) as max_id FROM customers")
                        result = cursor.fetchone()
                        next_cust_id = (result['max_id'] or 0) + 1
                        customer_code = f"CUST{next_cust_id:06d}"
                        
                        cursor.execute("""
                            INSERT INTO customers (customer_code, contact_person, phone, email, city, state, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """, (customer_code, cust_name, cust_phone[:15], cust_email, cust_city, cust_state))
                        customer_id = cursor.lastrowid
                    else:
                        customer_id = customer['id']
                    
                    # Check for duplicate ticket
                    cursor.execute("""
                        SELECT id FROM service_tickets 
                        WHERE customer_id=%s AND issue_description=%s AND DATE(created_at)=DATE(%s)
                        LIMIT 1
                    """, (customer_id, issue_desc, datetime.now()))
                    if cursor.fetchone():
                        errors.append(f"Row {idx+2}: Duplicate ticket for '{cust_name}' with same issue today")
                        continue
                    
                    product_id = None
                    if pd.notna(row.get('Product Model')):
                        cursor.execute("SELECT id FROM products WHERE name=%s LIMIT 1", (row.get('Product Model'),))
                        product = cursor.fetchone()
                        if product:
                            product_id = product['id']
                    
                    engineer_id = None
                    engineer_name = row.get('Name of the Service Engineer Assigned', '')
                    if pd.notna(engineer_name) and engineer_name:
                        names = str(engineer_name).split()
                        if len(names) >= 1:
                            cursor.execute("SELECT id FROM users WHERE first_name=%s LIMIT 1", (names[0],))
                            engineer = cursor.fetchone()
                            if engineer:
                                engineer_id = engineer['id']
                    
                    cursor.execute("SELECT MAX(id) as max_id FROM service_tickets")
                    result = cursor.fetchone()
                    next_id = (result['max_id'] or 0) + 1
                    ticket_number = f"TKT{next_id:06d}"
                    
                    priority_str = str(row.get('Issue priority', 'Medium')).strip().title()
                    priority_map = {'Low': 'LOW', 'Medium': 'MEDIUM', 'High': 'HIGH', 'Critical': 'CRITICAL'}
                    priority = priority_map.get(priority_str, 'MEDIUM')
                    
                    status_str = str(row.get('Status', 'Open')).strip().title()
                    status_map = {'Open': 'OPEN', 'In Progress': 'IN_PROGRESS', 'Completed': 'CLOSED', 'Closed': 'CLOSED', 'Resolved': 'RESOLVED'}
                    status = status_map.get(status_str, 'OPEN')
                    
                    warranty = str(row.get('Within Warranty or OUT side Warranty', 'NO')).strip().upper()
                    warranty_status = 'Yes' if warranty.startswith('YES') or warranty.startswith('WITHIN') else 'No'
                    
                    issue_date = datetime.now()
                    if pd.notna(row.get('Issue Reported Date')):
                        try:
                            issue_date = pd.to_datetime(row.get('Issue Reported Date'), dayfirst=True)
                        except:
                            pass
                    
                    cursor.execute("""
                        INSERT INTO service_tickets 
                        (ticket_number, customer_id, product_id, issue_description, priority, status, 
                        assigned_staff_id, warranty_status, resolution_details, remarks, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ticket_number,
                        customer_id,
                        product_id,
                        row.get('Issue Reported', ''),
                        priority,
                        status,
                        engineer_id,
                        warranty_status,
                        row.get('Resolution Details', ''),
                        row.get('Remarks', ''),
                        issue_date
                    ))
                    imported += 1
                except Exception as e:
                    errors.append(f"Row {idx+2}: {str(e)}")
                    print(f"Import row {idx+2} error: {e}")
            
            conn.commit()
            conn.close()
            
            result = {
                'message': f'Imported {imported} of {len(df)} tickets',
                'imported': imported,
                'total': len(df),
                'errors': errors[:10]  # Limit to first 10 errors
            }
            print(f"Import complete: {result}")
            return jsonify(result)
            
        except Exception as e:
            error_msg = str(e)
            print(f"Import error: {error_msg}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': error_msg}), 500
