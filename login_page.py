from flask import request, jsonify
from flask_jwt_extended import create_access_token
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import pymysql
import hashlib
import bcrypt
import secrets
import time
from database import get_db, sanitize_input

# Simple rate limiting storage (in production, use Redis)
login_attempts = {}

def is_rate_limited(username):
    """Check if user is rate limited"""
    now = time.time()
    if username in login_attempts:
        attempts = login_attempts[username]
        # Remove old attempts (older than 15 minutes)
        attempts = [attempt for attempt in attempts if now - attempt < 900]
        login_attempts[username] = attempts
        
        # Check if too many attempts
        if len(attempts) >= 5:
            return True
    return False

def record_login_attempt(username):
    """Record a failed login attempt"""
    now = time.time()
    if username not in login_attempts:
        login_attempts[username] = []
    login_attempts[username].append(now)

def create_password_hash(password):
    """Create password hash in the same format as your database"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, stored_hash):
    """Verify password against stored hash - supports both bcrypt and SHA256"""
    try:
        # Check if it's bcrypt (starts with $2b$)
        if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$'):
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        # Check if it's SHA256 format (salt:hash)
        elif ':' in stored_hash:
            salt, hash_part = stored_hash.split(':', 1)
            password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
            return password_hash == hash_part
        else:
            # Plain text comparison as fallback
            return password == stored_hash
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def register_login_routes(app):
    """Register login page routes"""
    
    @app.route('/api/v1/auth/login', methods=['POST'])
    def login():
        try:
            print(f"Login attempt - Content-Type: {request.content_type}")
            print(f"Request data: {request.get_data()}")
            
            # Handle both JSON and form data
            if request.content_type == 'application/x-www-form-urlencoded':
                username = sanitize_input(request.form.get('username'))
                password = request.form.get('password')
                print(f"Form data - Username: {username}")
            else:
                data = request.get_json()
                print(f"JSON data: {data}")
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                username = sanitize_input(data.get('username'))
                password = data.get('password')
                print(f"JSON data - Username: {username}")
            
            # Enhanced Validation
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            # Username validation
            if len(username) < 3:
                return jsonify({'error': 'Username must be at least 3 characters'}), 400
            
            if len(username) > 50:
                return jsonify({'error': 'Username must be less than 50 characters'}), 400
            
            # Password validation
            if len(password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters'}), 400
            
            if len(password) > 100:
                return jsonify({'error': 'Password must be less than 100 characters'}), 400
            
            # Security: Check for SQL injection patterns
            dangerous_patterns = ['--', ';', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
            username_upper = username.upper()
            for pattern in dangerous_patterns:
                if pattern in username_upper:
                    return jsonify({'error': 'Invalid characters in username'}), 400
            
            print(f"Attempting login for: {username}")
            
            # Rate limiting check
            if is_rate_limited(username):
                return jsonify({
                    'error': 'Too many login attempts. Please try again in 15 minutes.'
                }), 429
            
            # Hardcoded admin (as per README)
            if username == 'admin' and password == 'admin123':
                print("Admin login successful")
                token = create_access_token(identity={
                    'id': 1, 
                    'username': 'admin', 
                    'role': 'admin',
                    'first_name': 'Admin',
                    'last_name': 'User'
                })
                return jsonify({
                    'access_token': token,
                    'token_type': 'bearer',
                    'user': {
                        'id': 1, 
                        'username': 'admin', 
                        'role': 'admin', 
                        'first_name': 'Admin', 
                        'last_name': 'User',
                        'email': 'admin@ostrich.com'
                    }
                })
            
            print("Admin login failed - checking database users")
            
            # Database users
            conn = get_db()
            if conn:
                try:
                    cursor = conn.cursor(pymysql.cursors.DictCursor)
                    
                    # First, let's see what users exist
                    cursor.execute("SELECT username, role, is_active FROM users LIMIT 10")
                    all_users = cursor.fetchall()
                    print(f"Available users in database: {all_users}")
                    
                    cursor.execute("""
                        SELECT id, username, first_name, last_name, email, role, password_hash
                        FROM users 
                        WHERE username = %s AND is_active = 1
                    """, (username,))
                    user = cursor.fetchone()
                    
                    if user:
                        print(f"Database user found: {user['username']} - Role: {user['role']}")
                        
                        # Verify password using custom hash format
                        stored_password_hash = user.get('password_hash')
                        
                        if stored_password_hash:
                            password_valid = verify_password(password, stored_password_hash)
                            print(f"Password verification result: {password_valid}")
                        else:
                            print("No password hash found")
                            password_valid = False
                        
                        if password_valid:
                            print("Password verification successful")
                            cursor.execute(
                                "UPDATE users SET last_login = %s WHERE id = %s",
                                (datetime.now(), user['id'])
                            )
                            conn.commit()
                            
                            # Remove password_hash from response
                            user_data = {
                                'id': user['id'],
                                'username': user['username'],
                                'first_name': user['first_name'],
                                'last_name': user['last_name'],
                                'email': user['email'],
                                'role': user['role']
                            }
                            
                            token = create_access_token(identity=user_data)
                            return jsonify({
                                'access_token': token,
                                'token_type': 'bearer',
                                'user': user_data
                            })
                        else:
                            print("Password verification failed")
                    else:
                        print(f"No database user found with username: {username}")
                finally:
                    conn.close()
            else:
                print("Database connection failed")
            
            print("Login failed - invalid credentials")
            # Record failed attempt for rate limiting
            record_login_attempt(username)
            return jsonify({'error': 'Invalid credentials'}), 401
            
        except Exception as e:
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Login failed'}), 500
    
    @app.route('/api/v1/auth/me', methods=['GET'])
    @jwt_required()
    def get_current_user():
        return jsonify({'user': get_jwt_identity()})
    
    @app.route('/api/v1/auth/logout', methods=['POST'])
    @jwt_required()
    def logout():
        return jsonify({'message': 'Logged out successfully'})
    
    @app.route('/api/v1/notifications/unread-count', methods=['GET'])
    def get_unread_notifications_count():
        return jsonify({'unread_count': 0})