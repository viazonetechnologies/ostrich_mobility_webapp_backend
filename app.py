from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
<<<<<<< HEAD
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
=======
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)  # 7 days
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)  # 30 days
>>>>>>> b95dea8cbabfb72d88454cae8b2b114526b16086

# Initialize extensions
jwt = JWTManager(app)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
<<<<<<< HEAD
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token is missing'}), 401

CORS(app, 
     origins=['*'],
=======
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
    'https://ostrich-mobility-webapp-frontend-cv3rmupqy.vercel.app'
]

CORS(app, 
     origins=allowed_origins, 
>>>>>>> b95dea8cbabfb72d88454cae8b2b114526b16086
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

<<<<<<< HEAD
# Explicitly add the Vercel frontend URL
ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://ostrich-mobility-webapp-frontend-3lxjrmef8.vercel.app',
    'https://ostrich-mobility-webapp-frontend.vercel.app',
    'https://ostrich-mobility-webapp-frontend-emaeg8you.vercel.app',
    'https://ostrich-mobility-webapp-frontend-40riormqu.vercel.app',
    'https://ostrich-mobility-webapp-frontend-hjetropff.vercel.app'
]

=======
>>>>>>> b95dea8cbabfb72d88454cae8b2b114526b16086
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
<<<<<<< HEAD
        response.headers.add("Access-Control-Allow-Origin", origin or "*")
=======
        if origin in allowed_origins:
            response.headers.add("Access-Control-Allow-Origin", origin)
>>>>>>> b95dea8cbabfb72d88454cae8b2b114526b16086
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,POST,PUT,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

<<<<<<< HEAD
# Add CORS headers to all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin and origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Import and register routes
try:
    from login_page import register_login_routes
    register_login_routes(app)
except Exception as e:
    print(f"Error loading login_page: {e}")

try:
    from dashboard_page import register_dashboard_routes
    register_dashboard_routes(app)
except Exception as e:
    print(f"Error loading dashboard_page: {e}")

try:
    from customers_page import register_customers_routes
    register_customers_routes(app)
except Exception as e:
    print(f"Error loading customers_page: {e}")

try:
    from enhanced_categories_page import register_categories_routes
    register_categories_routes(app)
except Exception as e:
    print(f"Error loading enhanced_categories_page: {e}")

try:
    from products_page import register_products_routes
    register_products_routes(app)
except Exception as e:
    print(f"Error loading products_page: {e}")

try:
    from service_tickets_page import register_service_tickets_routes
    register_service_tickets_routes(app)
    print("✓ service_tickets_page loaded successfully")
except Exception as e:
    print(f"Error loading service_tickets_page: {e}")
    # Add fallback route
    @app.route('/api/v1/service-tickets/', methods=['GET'])
    def fallback_service_tickets():
        return jsonify({'error': 'Service tickets module failed to load', 'details': str(e)}), 503

try:
    from stock_fix_routes import register_stock_fix_routes
    register_stock_fix_routes(app)
except Exception as e:
    print(f"Error loading stock_fix_routes: {e}")

try:
    from customer_auth import register_customer_auth_routes
    register_customer_auth_routes(app)
except Exception as e:
    print(f"Error loading customer_auth: {e}")

try:
    from product_images_routes import register_product_images_routes as register_product_images_api_routes
    register_product_images_api_routes(app)
except Exception as e:
    print(f"Error loading product_images_routes: {e}")

try:
    from regions_page import register_regions_routes
    register_regions_routes(app)
except Exception as e:
    print(f"Error loading regions_page: {e}")

try:
    from users_page import register_users_routes
    register_users_routes(app)
except Exception as e:
    print(f"Error loading users_page: {e}")

try:
    from profile_page import register_profile_routes
    register_profile_routes(app)
except Exception as e:
    print(f"Error loading profile_page: {e}")

try:
    from all_routes import (register_product_images_routes, register_enquiries_routes,
                           register_service_routes, register_sales_routes,
                           register_dispatch_routes, register_reports_routes,
                           register_notifications_routes, register_specifications_routes)
    register_product_images_routes(app)
    register_enquiries_routes(app)
    register_service_routes(app)
    register_sales_routes(app)
    register_dispatch_routes(app)
    register_reports_routes(app)
    register_notifications_routes(app)
    register_specifications_routes(app)
except Exception as e:
    print(f"Error loading all_routes: {e}")

# Health check
=======
# Import all routes from consolidated file
from all_routes import (
    register_product_images_routes as register_product_images_basic,
    register_enquiries_routes,
    register_service_routes,
    register_sales_routes,
    register_dispatch_routes,
    register_reports_routes,
    register_notifications_routes,
    register_specifications_routes,
    register_all_imported_routes
)
from stock_fix_routes import register_stock_fix_routes
from customer_auth import register_customer_auth_routes
from product_images_routes import register_product_images_routes as register_product_images_advanced

# Register all routes
register_product_images_basic(app)  # Basic product images routes from all_routes.py
register_enquiries_routes(app)
register_service_routes(app)
register_sales_routes(app)
register_dispatch_routes(app)
register_reports_routes(app)
register_notifications_routes(app)
register_specifications_routes(app)
register_stock_fix_routes(app)
register_customer_auth_routes(app)
register_product_images_advanced(app)  # Advanced product images routes from product_images_routes.py
register_all_imported_routes(app)  # Routes from separate page files

# Health check
@app.route('/')
def root():
    return {'message': 'Ostrich Mobility Backend API', 'status': 'running', 'version': '1.0'}

>>>>>>> b95dea8cbabfb72d88454cae8b2b114526b16086
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
<<<<<<< HEAD
    print("Starting Ostrich Web App Backend... v2.1")  # Force reload
    print("Login: admin / admin123")
    print("Server: http://localhost:8002")
    print("Available endpoints:")
    print("- POST /api/v1/auth/login")
    print("- GET /api/v1/dashboard/analytics")
    print("- GET /api/v1/notifications/unread-count")
    app.run(debug=True, host='0.0.0.0', port=8002)
=======
    port = int(os.getenv('PORT', 8002))
    print("Starting Ostrich Web App Backend...")
    print(f"Server: http://0.0.0.0:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)
>>>>>>> b95dea8cbabfb72d88454cae8b2b114526b16086
