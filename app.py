from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)  # 7 days
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)  # 30 days

# Initialize extensions
jwt = JWTManager(app)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired', 'code': 'token_expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token', 'code': 'invalid_token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token is missing', 'code': 'missing_token'}), 401

# CORS configuration - allow frontend domain
allowed_origins = [
    'http://localhost:3000',
    'https://ostrich-mobility-webapp-frontend-iv7a1q5ru.vercel.app',
    'https://ostrich-mobility-webapp-frontend.vercel.app',
    'https://ostrich-mobility-webapp-frontend-cv3rmupqy.vercel.app',
    'https://ostrich-mobility-webapp-frontend-hvozi4x6l.vercel.app'
]

CORS(app, 
     origins=allowed_origins, 
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Static file serving
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return jsonify({'error': 'File not found'}), 404

@app.route('/uploads/products/<filename>')
def serve_product_image(filename):
    return jsonify({'error': 'Images served from cloud'}), 404

# Handle preflight requests globally
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        origin = request.headers.get('Origin')
        if origin in allowed_origins:
            response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,POST,PUT,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

# Import all routes from consolidated file
from all_routes import (
    register_product_images_routes as register_product_images_basic,
    register_enquiries_routes,
    register_service_routes,
    register_sales_routes,
    register_dispatch_routes,
    register_reports_routes,
    register_notifications_routes,
    register_specifications_routes
)
from stock_fix_routes import register_stock_fix_routes
from customer_auth import register_customer_auth_routes
from product_images_routes import register_product_images_routes as register_product_images_advanced

try:
    from login_page import register_login_routes
    from dashboard_page import register_dashboard_routes
    from categories_page import register_categories_routes
    from customers_page import register_customers_routes
    from products_page import register_products_routes
    from users_page import register_users_routes
    from profile_page import register_profile_routes
    from regions_page import register_regions_routes
    
    # Register all routes
    register_login_routes(app)
    register_dashboard_routes(app)
    register_categories_routes(app)
    register_customers_routes(app)
    register_products_routes(app)
    register_users_routes(app)
    register_profile_routes(app)
    register_regions_routes(app)
    print("✓ Page routes registered")
except Exception as e:
    print(f"Page routes import error: {e}")
    import traceback
    traceback.print_exc()

register_product_images_basic(app)
register_enquiries_routes(app)
register_service_routes(app)
register_sales_routes(app)
register_dispatch_routes(app)
register_reports_routes(app)
register_notifications_routes(app)
register_specifications_routes(app)
register_stock_fix_routes(app)
register_customer_auth_routes(app)
register_product_images_advanced(app)

# Service tickets routes - inline implementation
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql

@app.route('/api/v1/service-tickets/', methods=['GET', 'POST'])
@jwt_required(optional=True)
def handle_service_tickets():
    if request.method == 'GET':
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT st.*, c.contact_person as customer_name, c.phone as customer_phone,
                       c.email as customer_email, c.city as customer_city, c.state as customer_state,
                       p.name as product_name, pc.name as product_category,
                       u.first_name as engineer_first_name, u.last_name as engineer_last_name
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
    
    elif request.method == 'POST':
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
                ticket_number, data.get('customer_id'), data.get('product_id'),
                data.get('issue_description'), data.get('priority', 'MEDIUM'),
                data.get('status', 'OPEN'), data.get('assigned_staff_id'),
                data.get('warranty_status', 'No'), data.get('resolution_details'),
                data.get('remarks')
            ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Service ticket created', 'ticket_number': ticket_number})
        except Exception as e:
            print(f"Create service ticket error: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/v1/service-tickets/<int:ticket_id>', methods=['PUT', 'DELETE'])
@jwt_required(optional=True)
def handle_single_service_ticket(ticket_id):
    if request.method == 'PUT':
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
                data.get('customer_id'), data.get('product_id'), data.get('issue_description'),
                data.get('priority'), data.get('status'), data.get('assigned_staff_id'),
                data.get('warranty_status'), data.get('resolution_details'), data.get('remarks'),
                ticket_id
            ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Service ticket updated'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM service_tickets WHERE id=%s", (ticket_id,))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Service ticket deleted'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Health check
@app.route('/')
def root():
    return {'message': 'Ostrich Mobility Backend API', 'status': 'running', 'version': '1.0'}

@app.route('/api/v1/health')
def health_check():
    from datetime import datetime
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

# Debug endpoint to test validation without JWT
@app.route('/api/v1/test-validation', methods=['POST'])
def test_validation():
    data = request.get_json()
    
    # Test the same validation logic
    if not data.get('customer_id'):
        return jsonify({'error': 'Customer is required'}), 400
    
    status = data.get('status', 'new')
    valid_statuses = ['new', 'contacted', 'quoted', 'converted', 'closed']
    if status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
    
    # Test date validation
    if data.get('follow_up_date'):
        try:
            from datetime import datetime
            date_str = data['follow_up_date']
            if 'T' in date_str:
                follow_up_date = datetime.fromisoformat(date_str.replace('Z', ''))
            else:
                follow_up_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Validate date is not in the past (allow today)
            today = datetime.now().date()
            if follow_up_date.date() < today:
                return jsonify({'error': 'Follow-up date cannot be in the past'}), 400
                
        except ValueError:
            return jsonify({'error': 'Invalid follow-up date format. Use YYYY-MM-DD'}), 400
        except Exception as e:
            return jsonify({'error': 'Invalid follow-up date'}), 400
    
    return jsonify({'message': 'Validation passed', 'server': 'webappbackend'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8002))
    print("Starting Ostrich Web App Backend...")
    print(f"Server: http://0.0.0.0:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)
