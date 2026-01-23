from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
import pymysql
import bcrypt

def register_profile_routes(app):
    
    @app.route('/api/v1/profile/', methods=['GET'])
    @jwt_required()
    def get_profile():
        try:
            current_user_id = get_jwt_identity()
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, username, email, role, first_name, last_name, 
                       phone, region, is_active, last_login, created_at
                FROM users WHERE id = %s
            """, (current_user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if not user or not isinstance(user, dict):
                return jsonify({'error': 'User not found'}), 404
            
            # Ensure role is not None
            if not user.get('role'):
                user['role'] = 'user'
            
            return jsonify(user)
        except Exception as e:
            print(f"Get profile error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/profile/', methods=['PUT'])
    @jwt_required()
    def update_profile():
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            # Validation
            if not data.get('first_name') or len(data['first_name'].strip()) < 2:
                return jsonify({
                    'error': 'First name must be at least 2 characters',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'First name must be at least 2 characters'}
                }), 400
            
            if not data.get('last_name') or len(data['last_name'].strip()) < 2:
                return jsonify({
                    'error': 'Last name must be at least 2 characters',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'Last name must be at least 2 characters'}
                }), 400
            
            # Email validation
            import re
            email = data.get('email', '').strip()
            if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                return jsonify({
                    'error': 'Invalid email format',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'Invalid email format'}
                }), 400
            
            # Phone validation
            phone = data.get('phone', '').strip()
            if phone:
                phone_digits = re.sub(r'\D', '', phone)
                if len(phone_digits) != 10 or phone_digits[0] not in '6789':
                    return jsonify({
                        'error': 'Phone must be 10 digits starting with 6, 7, 8, or 9',
                        'toast': {'type': 'danger', 'title': 'Error', 'message': 'Invalid phone number'}
                    }), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if email is taken by another user
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, current_user_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({
                    'error': 'Email already in use',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'Email already in use'}
                }), 400
            
            cursor.execute("""
                UPDATE users 
                SET first_name = %s, last_name = %s, email = %s, phone = %s
                WHERE id = %s
            """, (
                data['first_name'].strip(),
                data['last_name'].strip(),
                email,
                phone_digits if phone else None,
                current_user_id
            ))
            conn.commit()
            conn.close()
            
            return jsonify({
                'message': 'Profile updated successfully',
                'toast': {'type': 'success', 'title': 'Success', 'message': 'Profile updated successfully'}
            })
        except Exception as e:
            print(f"Update profile error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/profile/change-password', methods=['PUT'])
    @jwt_required()
    def change_password():
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            print(f"DEBUG: Received data: {data}")
            print(f"DEBUG: User ID: {current_user_id}")
            
            current_password = data.get('current_password', '').strip()
            new_password = data.get('new_password', '').strip()
            
            print(f"DEBUG: Current password length: {len(current_password)}")
            print(f"DEBUG: New password length: {len(new_password)}")
            
            # Validation
            if not current_password:
                print("DEBUG: Current password is empty")
                return jsonify({
                    'error': 'Current password is required',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'Current password is required'}
                }), 400
            
            if not new_password:
                print("DEBUG: New password is empty")
                return jsonify({
                    'error': 'New password is required',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'New password is required'}
                }), 400
            
            if len(new_password) < 6:
                print(f"DEBUG: New password too short: {len(new_password)}")
                return jsonify({
                    'error': 'New password must be at least 6 characters',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'Password must be at least 6 characters'}
                }), 400
            
            if current_password == new_password:
                print("DEBUG: Passwords are the same")
                return jsonify({
                    'error': 'New password must be different from current password',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'New password must be different'}
                }), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (current_user_id,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return jsonify({'error': 'User not found'}), 404
            
            # Verify current password
            password_hash = user['password_hash']
            print(f"DEBUG: Password hash starts with: {password_hash[:10]}")
            
            password_valid = False
            
            # Check if it's bcrypt (starts with $2b$ or $2a$ or $2y$)
            if password_hash.startswith('$2'):
                print("DEBUG: Using bcrypt verification")
                try:
                    password_valid = bcrypt.checkpw(current_password.encode('utf-8'), password_hash.encode('utf-8'))
                except Exception as e:
                    print(f"DEBUG: Bcrypt error: {e}")
            # Check if it's SHA256 with salt (salt:hash format)
            elif ':' in password_hash:
                print("DEBUG: Using SHA256 with salt verification")
                import hashlib
                salt, hash_part = password_hash.split(':', 1)
                computed_hash = hashlib.sha256((salt + current_password).encode()).hexdigest()
                password_valid = computed_hash == hash_part
            else:
                print("DEBUG: Using plain SHA256 verification")
                # Plain SHA256 without salt
                import hashlib
                computed_hash = hashlib.sha256(current_password.encode()).hexdigest()
                password_valid = computed_hash == password_hash
            
            if not password_valid:
                conn.close()
                print("DEBUG: Password verification failed")
                return jsonify({
                    'error': 'Current password is incorrect',
                    'toast': {'type': 'danger', 'title': 'Error', 'message': 'Current password is incorrect'}
                }), 400
            
            print("DEBUG: Password verified, updating...")
            # Hash new password
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # Update password
            cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, current_user_id))
            conn.commit()
            conn.close()
            
            print("DEBUG: Password updated successfully")
            return jsonify({
                'message': 'Password changed successfully',
                'toast': {'type': 'success', 'title': 'Success', 'message': 'Password changed successfully'}
            })
        except Exception as e:
            print(f"Change password error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
