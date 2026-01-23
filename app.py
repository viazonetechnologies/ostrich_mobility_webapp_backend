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
    print(f"Token expired: {jwt_payload}")
    return jsonify({'error': 'Token has expired', 'code': 'token_expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"Invalid token error: {error}")
    return jsonify({'error': 'Invalid token', 'code': 'invalid_token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"Missing token error: {error}")
    return jsonify({'error': 'Authorization token is missing', 'code': 'missing_token'}), 401

# CORS configuration - allow frontend domain
allowed_origins = [
    'http://localhost:3000',
    'https://ostrich-mobility-webapp-frontend-f57owg3kj.vercel.app',
    'https://ostrich-mobility-webapp-frontend.vercel.app',
    'https://ostrich-mobility-webapp-frontend-cv3rmupqy.vercel.app',
    'https://ostrich-mobility-webapp-frontend-qn0i03c1c.vercel.app',
    'https://ostrich-mobility-webapp-frontend-9oji7dzwn.vercel.app',
    'https://ostrich-mobility-webapp-frontend-lqsbudnrz.vercel.app'
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
