from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import secrets
from functools import wraps
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
import threading
import time

# Import optimized components
from optimized_db import get_optimized_db_connection, webapp_db_pool
from webapp_cache import webapp_cache, cache_key

# Import the dispatch validator
from dispatch_validator import DispatchValidator, DispatchDataCleaner

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=False, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])

# Background cleanup task for webapp
def webapp_cleanup_task():
    """Background task to cleanup cache and connections"""
    while True:
        time.sleep(180)  # Run every 3 minutes for webapp
        webapp_cache.cleanup_expired()
        webapp_db_pool.cleanup_idle_connections()

# Start cleanup thread
webapp_cleanup_thread = threading.Thread(target=webapp_cleanup_task, daemon=True)
webapp_cleanup_thread.start()

# Image upload configuration
UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SECRET_KEY'] = SECRET_KEY

# JWT utilities
def create_access_token(data):
    payload = data.copy()
    payload['exp'] = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Auth decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
            payload = verify_token(token)
            if payload:
                return f(current_user=payload, *args, **kwargs)
        
        print(f"Unauthorized request to {request.path}: {request.headers.get('Authorization', 'No token')}")
        return jsonify({'error': 'Token required'}), 401
    return decorated

# Optimized database helper functions
def execute_cached_query(query, params=None, cache_key_name=None, ttl=180, fetch_one=False):
    """Execute query with caching"""
    if cache_key_name:
        cached_result = webapp_cache.get(cache_key_name)
        if cached_result is not None:
            return cached_result
    
    try:
        with get_optimized_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute(query, params or [])
                
                if fetch_one:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
                
                # Cache the result
                if cache_key_name and result:
                    webapp_cache.set(cache_key_name, result, ttl)
                
                return result
    except Exception as e:
        print(f"Database query failed: {e}")
    return None

# In-memory storage for demo (with caching)
def get_cached_users():
    cache_k = cache_key("users", "all")
    cached = webapp_cache.get(cache_k)
    if cached:
        return cached
    
    users = {
        "superadmin": {"id": 1, "username": "superadmin", "password": "super123", "role": "super_admin"},
        "admin": {"id": 2, "username": "admin", "password": "admin123", "role": "admin"},
        "regional_office": {"id": 3, "username": "regional_office", "password": "regional123", "role": "regional_office"},
        "manager": {"id": 4, "username": "manager", "password": "manager123", "role": "manager"},
        "sales_executive": {"id": 5, "username": "sales_executive", "password": "sales123", "role": "sales_executive"},
        "service_staff": {"id": 6, "username": "service_staff", "password": "service123", "role": "service_staff"}
    }
    webapp_cache.set(cache_k, users, 600)  # Cache for 10 minutes
    return users

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Health check with performance info
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "optimizations": {
            "connection_pooling": "enabled",
            "caching": "enabled",
            "background_cleanup": "enabled"
        },
        "pool_stats": {
            "active_connections": len(webapp_db_pool.pool),
            "max_connections": webapp_db_pool.max_connections
        }
    })

# Optimized database test
@app.route('/db-test')
def db_test():
    try:
        with get_optimized_db_connection() as conn:
            if conn is None:
                return jsonify({"status": "failed", "error": "No connection"})
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            customer_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM enquiries")
            enquiry_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM service_tickets")
            service_count = cursor.fetchone()['count']
            
            return jsonify({
                "status": "success",
                "customers": customer_count,
                "enquiries": enquiry_count,
                "service_tickets": service_count,
                "connection_pool": "optimized"
            })
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)})

# Serve uploaded files
@app.route('/static/uploads/products/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return jsonify({"error": "File not found"}), 404

# Global OPTIONS handler for all routes
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    # Skip auth for certain endpoints
    skip_auth_paths = ['/static/', '/api/v1/products/', '/images', '/health', '/db-test', '/debug', '/test']
    if any(request.path.startswith(path) for path in skip_auth_paths):
        return
    
    # Skip auth for login endpoints
    if 'login' in request.path:
        return

# Auth endpoints (optimized)
@app.route('/api/v1/auth/login', methods=['POST', 'OPTIONS'])
@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    username = request.form.get('username') or (request.get_json(silent=True) or {}).get('username')
    password = request.form.get('password') or (request.get_json(silent=True) or {}).get('password')
    
    # TEMPORARY: Allow any login for testing
    if username and password:
        access_token = create_access_token({"sub": "1"})
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": username,
                "role": "admin"
            }
        })
    
    # Check demo users with caching
    users = get_cached_users()
    for user_key, user_data in users.items():
        if username == user_data["username"] and password == user_data["password"]:
            access_token = create_access_token({"sub": str(user_data["id"])})
            return jsonify({
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "role": user_data["role"]
                }
            })
    
    return jsonify({"detail": "Invalid credentials"}), 401

# Optimized customers endpoint
@app.route('/api/v1/customers/', methods=['GET'])
@app.route('/customers/', methods=['GET'])
@token_required
def read_customers(current_user):
    cache_k = cache_key("customers", "list")
    cached_result = webapp_cache.get(cache_k)
    if cached_result:
        return jsonify(cached_result)
    
    try:
        with get_optimized_db_connection() as conn:
            if conn is None:
                return jsonify({"message": "Database connection failed"}), 500
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers LIMIT 100")
            customers_db = cursor.fetchall()
            
            result = []
            for customer in customers_db:
                result.append({
                    "id": customer[0],
                    "customer_code": customer[1],
                    "customer_type": customer[2],
                    "company_name": customer[3],
                    "contact_person": customer[4],
                    "email": customer[5],
                    "phone": customer[6],
                    "address": customer[7],
                    "city": customer[8],
                    "state": customer[9],
                    "country": customer[10],
                    "pin_code": customer[11],
                    "status": 'active',
                    "created_at": str(customer[17]) if len(customer) > 17 else None
                })
            
            # Cache for 5 minutes
            webapp_cache.set(cache_k, result, 300)
            return jsonify(result)
    except Exception as e:
        print(f"Database error in customers: {e}")
        return jsonify([])

# Performance monitoring endpoint
@app.route('/api/v1/performance/stats')
@token_required
def performance_stats(current_user):
    return jsonify({
        "database": {
            "pool_size": len(webapp_db_pool.pool),
            "max_connections": webapp_db_pool.max_connections,
            "pool_utilization": f"{(len(webapp_db_pool.pool) / webapp_db_pool.max_connections) * 100:.1f}%"
        },
        "cache": {
            "enabled": True,
            "default_ttl": webapp_cache.default_ttl,
            "cache_size": len(webapp_cache.cache)
        },
        "optimizations": [
            "Connection pooling enabled",
            "Query result caching enabled", 
            "Background cleanup running",
            "Fallback database support"
        ]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    print("🚀 Starting Optimized Ostrich Webapp Backend")
    print(f"📊 Connection pool: {webapp_db_pool.max_connections} max connections")
    print(f"💾 Cache TTL: {webapp_cache.default_ttl} seconds")
    print(f"🔧 Background cleanup: Every 3 minutes")
    app.run(host='0.0.0.0', port=port, debug=False)