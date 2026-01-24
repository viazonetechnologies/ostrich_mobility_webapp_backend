from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
import pymysql
import bcrypt
import re

# Role hierarchy (higher number = more power)
ROLE_HIERARCHY = {
    'super_admin': 6,
    'admin': 5,
    'regional_officer': 4,
    'manager': 3,
    'sales_executive': 0,  # Cannot manage anyone
    'service_staff': 0  # Cannot manage anyone
}

def can_manage_user(current_role, target_role):
    """Check if current user can manage target user based on hierarchy"""
    current_level = ROLE_HIERARCHY.get(current_role, 0)
    target_level = ROLE_HIERARCHY.get(target_role, 0)
    # Must have higher level to manage
    return current_level > target_level

def register_users_routes(app):
    
    @app.route('/api/v1/users/', methods=['GET', 'POST'])
    @jwt_required()
    def handle_users():
        current_user_id = get_jwt_identity()
        
        # Get current user's role from database
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        conn.close()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        current_role = current_user['role']
        
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                role_filter = request.args.get('role')
                
                if role_filter:
                    cursor.execute("""
                        SELECT id, username, email, role, first_name, last_name, 
                               phone, region, is_active, last_login, created_at
                        FROM users 
                        WHERE role = %s
                        ORDER BY created_at DESC
                    """, (role_filter,))
                else:
                    cursor.execute("""
                        SELECT id, username, email, role, first_name, last_name, 
                               phone, region, is_active, last_login, created_at
                        FROM users 
                        ORDER BY created_at DESC
                    """)
                users = cursor.fetchall()
                conn.close()
                
                return jsonify(users)
            except Exception as e:
                print(f"Get users error: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                print(f"DEBUG: Received user data: {data}")
                
                # Check if current user can create users with the requested role
                requested_role = data.get('role', 'sales_executive')
                if not can_manage_user(current_role, requested_role):
                    return jsonify({'error': f'You cannot create users with role {requested_role}'}), 403
                
                # Validation with detailed error messages
                errors = []
                
                if not data.get('username'):
                    errors.append('Username is required')
                elif len(data['username']) < 3:
                    errors.append('Username must be at least 3 characters')
                elif len(data['username']) > 50:
                    errors.append('Username must be less than 50 characters')
                
                if not data.get('email'):
                    errors.append('Email is required')
                elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', data['email']):
                    errors.append('Invalid email format')
                
                if not data.get('password'):
                    errors.append('Password is required')
                elif len(data['password']) < 6:
                    errors.append('Password must be at least 6 characters')
                
                if not data.get('first_name'):
                    errors.append('First name is required')
                elif len(data['first_name']) < 2:
                    errors.append('First name must be at least 2 characters')
                
                if not data.get('last_name'):
                    errors.append('Last name is required')
                elif len(data['last_name']) < 2:
                    errors.append('Last name must be at least 2 characters')
                
                if not data.get('phone'):
                    errors.append('Phone is required')
                else:
                    phone = re.sub(r'\D', '', data['phone'])
                    if len(phone) != 10:
                        errors.append('Phone must be exactly 10 digits')
                    elif phone[0] not in '6789':
                        errors.append('Phone must start with 6, 7, 8, or 9')
                
                if errors:
                    error_msg = '; '.join(errors)
                    print(f"ERROR: Validation failed - {error_msg}")
                    return jsonify({'error': error_msg}), 400
                
                # Clean phone number
                phone = re.sub(r'\D', '', data['phone'])
                print(f"DEBUG: Cleaned phone: {phone}")
                
                conn = get_db()
                if not conn:
                    print("ERROR: Database connection failed")
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor()
                
                # Check if username exists
                cursor.execute("SELECT id FROM users WHERE username = %s", (data['username'],))
                if cursor.fetchone():
                    conn.close()
                    print(f"ERROR: Username '{data['username']}' already exists")
                    return jsonify({'error': 'Username already exists'}), 400
                
                # Check if email exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
                if cursor.fetchone():
                    conn.close()
                    print(f"ERROR: Email '{data['email']}' already exists")
                    return jsonify({'error': 'Email already exists'}), 400
                
                print("DEBUG: Hashing password...")
                # Hash password
                hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
                
                print(f"DEBUG: Inserting user with phone: {phone}")
                # Insert user
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, first_name, last_name, 
                                     phone, region, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data['username'],
                    data['email'],
                    hashed_password,
                    data.get('role', 'sales_executive'),
                    data['first_name'],
                    data['last_name'],
                    phone,
                    data.get('region'),
                    data.get('is_active', True)
                ))
                
                conn.commit()
                user_id = cursor.lastrowid
                conn.close()
                
                print(f"DEBUG: User created successfully with ID: {user_id}")
                return jsonify({'id': user_id, 'message': 'User created successfully'}), 201
            except Exception as e:
                print(f"Create user error: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
    @jwt_required()
    def handle_single_user(user_id):
        current_user_id = get_jwt_identity()
        
        # Get current user's role from database
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        conn.close()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        current_role = current_user['role']
        
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT id, username, email, role, first_name, last_name, 
                           phone, region, is_active, last_login, created_at
                    FROM users WHERE id = %s
                """, (user_id,))
                user = cursor.fetchone()
                conn.close()
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                return jsonify(user)
            except Exception as e:
                print(f"Get user error: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'PUT':
            try:
                # Get target user's role
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                target_user = cursor.fetchone()
                
                if not target_user:
                    conn.close()
                    return jsonify({'error': 'User not found'}), 404
                
                target_role = target_user['role']
                
                # Allow only super_admin and admin to edit themselves, or check hierarchy
                can_edit_self = current_user_id == user_id and current_role in ['super_admin', 'admin']
                if not can_edit_self and not can_manage_user(current_role, target_role):
                    conn.close()
                    return jsonify({'error': f'You cannot edit users with role {target_role}'}), 403
                
                conn.close()
                
                data = request.get_json()
                print(f"DEBUG: Updating user {user_id} with data: {data}")
                
                # Check if trying to change role to higher level (only if not super_admin/admin editing self)
                new_role = data.get('role', target_role)
                can_edit_self = current_user_id == user_id and current_role in ['super_admin', 'admin']
                if not can_edit_self and not can_manage_user(current_role, new_role):
                    return jsonify({'error': f'You cannot assign role {new_role}'}), 403
                
                # Validation with detailed error messages
                errors = []
                
                if not data.get('username'):
                    errors.append('Username is required')
                elif len(data['username']) < 3:
                    errors.append('Username must be at least 3 characters')
                elif len(data['username']) > 50:
                    errors.append('Username must be less than 50 characters')
                
                if not data.get('email'):
                    errors.append('Email is required')
                elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', data['email']):
                    errors.append('Invalid email format')
                
                if data.get('password') and len(data['password']) < 6:
                    errors.append('Password must be at least 6 characters')
                
                if not data.get('first_name'):
                    errors.append('First name is required')
                elif len(data['first_name']) < 2:
                    errors.append('First name must be at least 2 characters')
                
                if not data.get('last_name'):
                    errors.append('Last name is required')
                elif len(data['last_name']) < 2:
                    errors.append('Last name must be at least 2 characters')
                
                if not data.get('phone'):
                    errors.append('Phone is required')
                else:
                    phone = re.sub(r'\D', '', data['phone'])
                    if len(phone) != 10:
                        errors.append('Phone must be exactly 10 digits')
                    elif phone[0] not in '6789':
                        errors.append('Phone must start with 6, 7, 8, or 9')
                
                if errors:
                    error_msg = '; '.join(errors)
                    print(f"ERROR: Validation failed - {error_msg}")
                    return jsonify({'error': error_msg}), 400
                
                # Clean phone number
                phone = re.sub(r'\D', '', data['phone'])
                print(f"DEBUG: Cleaned phone: {phone}")
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'User not found'}), 404
                
                # Check if username is taken by another user
                cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", 
                             (data['username'], user_id))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'Username already exists'}), 400
                
                # Check if email is taken by another user
                cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", 
                             (data['email'], user_id))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'Email already exists'}), 400
                
                # Update user
                if data.get('password'):
                    # Hash new password
                    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
                    cursor.execute("""
                        UPDATE users 
                        SET username = %s, email = %s, password_hash = %s, role = %s, 
                            first_name = %s, last_name = %s, phone = %s, region = %s, is_active = %s
                        WHERE id = %s
                    """, (
                        data['username'],
                        data['email'],
                        hashed_password,
                        data.get('role', 'sales_executive'),
                        data['first_name'],
                        data['last_name'],
                        phone,
                        data.get('region'),
                        data.get('is_active', True),
                        user_id
                    ))
                else:
                    # Update without password
                    cursor.execute("""
                        UPDATE users 
                        SET username = %s, email = %s, role = %s, 
                            first_name = %s, last_name = %s, phone = %s, region = %s, is_active = %s
                        WHERE id = %s
                    """, (
                        data['username'],
                        data['email'],
                        data.get('role', 'sales_executive'),
                        data['first_name'],
                        data['last_name'],
                        phone,
                        data.get('region'),
                        data.get('is_active', True),
                        user_id
                    ))
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'User updated successfully'})
            except Exception as e:
                print(f"Update user error: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'DELETE':
            try:
                # Get target user's role
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                target_user = cursor.fetchone()
                
                if not target_user:
                    conn.close()
                    return jsonify({'error': 'User not found'}), 404
                
                target_role = target_user['role']
                
                # Check if current user can manage target user
                if not can_manage_user(current_role, target_role):
                    conn.close()
                    return jsonify({'error': f'You cannot delete users with role {target_role}'}), 403
                
                # Delete user
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'User deleted successfully'})
            except Exception as e:
                print(f"Delete user error: {e}")
                return jsonify({'error': str(e)}), 500
