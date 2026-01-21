from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
jwt = JWTManager(app)

# CORS configuration - allow frontend domain
allowed_origins = [
    'http://localhost:3000',
    'https://ostrich-mobility-webapp-frontend-iv7a1q5ru.vercel.app',
    'https://ostrich-mobility-webapp-frontend.vercel.app'
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

# Import page modules
from login_page import register_login_routes
from dashboard_page import register_dashboard_routes
from customers_page import register_customers_routes
from enhanced_categories_page import register_categories_routes
from products_page import register_products_routes
from service_tickets_page import register_service_tickets_routes
from stock_fix_routes import register_stock_fix_routes
from quick_fix import register_quick_fix_routes
from customer_auth import register_customer_auth_routes
from product_images_routes import register_product_images_routes as register_product_images_api_routes
from regions_page import register_regions_routes
from all_routes import *

# Register all page routes
register_login_routes(app)
register_dashboard_routes(app)
register_customers_routes(app)
register_categories_routes(app)
register_products_routes(app)
register_service_tickets_routes(app)
register_stock_fix_routes(app)
register_quick_fix_routes(app)
register_customer_auth_routes(app)
register_product_images_routes(app)  # from all_routes.py
register_product_images_api_routes(app)  # from product_images_routes.py
register_enquiries_routes(app)
register_users_routes(app)
register_profile_routes(app)
register_service_routes(app)
register_sales_routes(app)
register_dispatch_routes(app)
register_reports_routes(app)
register_notifications_routes(app)
register_specifications_routes(app)
register_regions_routes(app)

# Health check
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