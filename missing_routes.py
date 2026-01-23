from flask import jsonify, request
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql

def register_sales_routes(app):
    @app.route('/api/v1/sales/', methods=['GET', 'POST'])
    @jwt_required()
    def handle_sales():
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'sales': []})
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT s.*, c.company_name, c.contact_person, c.individual_name,
                           COUNT(si.id) as item_count
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    LEFT JOIN sale_items si ON s.id = si.sale_id
                    GROUP BY s.id
                    ORDER BY s.sale_date DESC
                """)
                sales = cursor.fetchall()
                conn.close()
                
                return jsonify({'sales': sales})
            except Exception as e:
                print(f"Get sales error: {e}")
                return jsonify({'sales': []})
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                conn = get_db()
                cursor = conn.cursor()
                
                # Generate sale number
                cursor.execute("SELECT sale_number FROM sales ORDER BY id DESC LIMIT 1")
                last_sale = cursor.fetchone()
                if last_sale and last_sale[0]:
                    last_num = int(last_sale[0][3:])
                    sale_number = f"SAL{str(last_num + 1).zfill(6)}"
                else:
                    sale_number = "SAL000001"
                
                cursor.execute("""
                    INSERT INTO sales (sale_number, customer_id, sale_date, total_amount, delivery_status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    sale_number, data['customer_id'], data['sale_date'],
                    data['total_amount'], data.get('delivery_status', 'pending')
                ))
                
                conn.commit()
                conn.close()
                return jsonify({'message': 'Sale created', 'sale_number': sale_number}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500

def register_dispatch_routes(app):
    @app.route('/api/v1/dispatch/', methods=['GET', 'POST'])
    @jwt_required()
    def handle_dispatch():
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT d.*, c.company_name, c.contact_person, p.name as product_name
                    FROM dispatches d
                    LEFT JOIN customers c ON d.customer_id = c.id
                    LEFT JOIN products p ON d.product_id = p.id
                    ORDER BY d.dispatch_date DESC
                """)
                dispatches = cursor.fetchall()
                conn.close()
                
                return jsonify(dispatches)
            except Exception as e:
                print(f"Get dispatches error: {e}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                conn = get_db()
                cursor = conn.cursor()
                
                # Generate dispatch number
                cursor.execute("SELECT dispatch_number FROM dispatches ORDER BY id DESC LIMIT 1")
                last_dispatch = cursor.fetchone()
                if last_dispatch and last_dispatch[0]:
                    last_num = int(last_dispatch[0][3:])
                    dispatch_number = f"DIS{str(last_num + 1).zfill(6)}"
                else:
                    dispatch_number = "DIS000001"
                
                cursor.execute("""
                    INSERT INTO dispatches (dispatch_number, customer_id, product_id, 
                                          dispatch_date, driver_name, vehicle_number, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    dispatch_number, data['customer_id'], data['product_id'],
                    data['dispatch_date'], data['driver_name'], data['vehicle_number'],
                    data.get('status', 'pending')
                ))
                
                conn.commit()
                conn.close()
                return jsonify({'message': 'Dispatch created', 'dispatch_number': dispatch_number}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500

def register_reports_routes(app):
    @app.route('/api/v1/reports/dashboard', methods=['GET'])
    @jwt_required()
    def get_dashboard_stats():
        try:
            conn = get_db()
            if not conn:
                return jsonify({})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get totals
            cursor.execute("SELECT COUNT(*) as customers FROM customers")
            customers = cursor.fetchone()['customers']
            
            cursor.execute("SELECT COUNT(*) as sales, COALESCE(SUM(total_amount), 0) as revenue FROM sales")
            sales_data = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) as dispatches FROM dispatches")
            dispatches = cursor.fetchone()['dispatches']
            
            # Get dispatch status breakdown
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM dispatches 
                GROUP BY status
            """)
            dispatch_status = cursor.fetchall()
            
            # Get sales delivery status
            cursor.execute("""
                SELECT delivery_status, COUNT(*) as count 
                FROM sales 
                GROUP BY delivery_status
            """)
            sales_delivery = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'totals': {
                    'customers': customers,
                    'sales': sales_data['sales'],
                    'revenue': float(sales_data['revenue']),
                    'dispatches': dispatches
                },
                'dispatch_status': dispatch_status,
                'sales_delivery': sales_delivery
            })
        except Exception as e:
            print(f"Dashboard stats error: {e}")
            return jsonify({})
    
    @app.route('/api/v1/reports/sales', methods=['GET'])
    @jwt_required()
    def get_sales_report():
        try:
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            cursor.execute("""
                SELECT s.*, c.company_name, c.contact_person,
                       COUNT(si.id) as item_count
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                LEFT JOIN sale_items si ON s.id = si.sale_id
                GROUP BY s.id
                ORDER BY s.sale_date DESC
            """)
            sales = cursor.fetchall()
            
            # Calculate summary
            total_sales = len(sales)
            total_revenue = sum(float(s['total_amount'] or 0) for s in sales)
            avg_sale = total_revenue / total_sales if total_sales > 0 else 0
            
            conn.close()
            
            return jsonify({
                'summary': {
                    'total_sales': total_sales,
                    'total_revenue': total_revenue,
                    'avg_sale_amount': avg_sale
                },
                'sales': sales
            })
        except Exception as e:
            return jsonify({'summary': {}, 'sales': []})
    
    @app.route('/api/v1/reports/dispatch', methods=['GET'])
    @jwt_required()
    def get_dispatch_report():
        try:
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            cursor.execute("""
                SELECT d.*, c.company_name, c.contact_person, p.name as product_name
                FROM dispatches d
                LEFT JOIN customers c ON d.customer_id = c.id
                LEFT JOIN products p ON d.product_id = p.id
                ORDER BY d.dispatch_date DESC
            """)
            dispatches = cursor.fetchall()
            
            # Calculate summary
            total_dispatches = len(dispatches)
            delivered_count = sum(1 for d in dispatches if d['status'] == 'delivered')
            in_transit_count = sum(1 for d in dispatches if d['status'] == 'in_transit')
            pending_count = sum(1 for d in dispatches if d['status'] == 'pending')
            cancelled_count = sum(1 for d in dispatches if d['status'] == 'cancelled')
            
            conn.close()
            
            return jsonify({
                'summary': {
                    'total_dispatches': total_dispatches,
                    'delivered_count': delivered_count,
                    'in_transit_count': in_transit_count,
                    'pending_count': pending_count,
                    'cancelled_count': cancelled_count
                },
                'dispatches': dispatches
            })
        except Exception as e:
            return jsonify({'summary': {}, 'dispatches': []})

def register_notifications_routes(app):
    @app.route('/api/v1/notifications/', methods=['GET'])
    @jwt_required()
    def get_notifications():
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT n.*, c.company_name as recipient_name
                FROM notifications n
                LEFT JOIN customers c ON n.customer_id = c.id
                ORDER BY n.created_at DESC
            """)
            notifications = cursor.fetchall()
            conn.close()
            
            return jsonify(notifications)
        except Exception as e:
            return jsonify([])
    
    @app.route('/api/v1/notifications/customers', methods=['GET'])
    @jwt_required()
    def get_notification_customers():
        try:
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, 
                       COALESCE(company_name, contact_person, individual_name) as name,
                       email, phone
                FROM customers
                ORDER BY name
            """)
            customers = cursor.fetchall()
            conn.close()
            return jsonify(customers)
        except Exception as e:
            return jsonify([])
    
    @app.route('/api/v1/notifications/unread-count', methods=['GET'])
    @jwt_required()
    def get_unread_count():
        return jsonify({'unread_count': 0})

def register_specifications_routes(app):
    @app.route('/api/v1/specifications/', methods=['GET'])
    @jwt_required()
    def get_specifications():
        try:
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT ps.*, p.name as product_name, p.product_code
                FROM product_specifications ps
                LEFT JOIN products p ON ps.product_id = p.id
                ORDER BY p.name, ps.spec_name
            """)
            specs = cursor.fetchall()
            conn.close()
            return jsonify(specs)
        except Exception as e:
            return jsonify([])

def register_service_routes(app):
    pass  # Already implemented in service_tickets_page.py