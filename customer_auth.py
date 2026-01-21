from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
import secrets
import string
from datetime import datetime, timedelta
from database import get_db, sanitize_input
import pymysql

def generate_password(length=8):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_customer_auth_routes(app):
    """Register customer authentication routes"""
    
    @app.route('/api/v1/customer/login', methods=['POST'])
    def customer_login():
        """Customer login endpoint"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            email_or_phone = data.get('email_or_phone', '').strip()
            password = data.get('password', '')
            
            if not email_or_phone or not password:
                return jsonify({'error': 'Email/phone and password are required'}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Find customer by email or phone
            cursor.execute("""
                SELECT id, customer_code, email, phone, contact_person, individual_name, 
                       password_hash, is_verified, customer_type
                FROM customers 
                WHERE (email = %s OR phone = %s) AND password_hash IS NOT NULL
            """, (email_or_phone, email_or_phone))
            
            customer = cursor.fetchone()
            conn.close()
            
            if not customer or not verify_password(password, customer['password_hash']):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Create access token
            access_token = create_access_token(
                identity=customer['id'],
                additional_claims={
                    'customer_code': customer['customer_code'],
                    'email': customer['email'],
                    'role': 'customer'
                }
            )
            
            return jsonify({
                'access_token': access_token,
                'customer': {
                    'id': customer['id'],
                    'customer_code': customer['customer_code'],
                    'email': customer['email'],
                    'phone': customer['phone'],
                    'name': customer['contact_person'] or customer['individual_name'],
                    'customer_type': customer['customer_type'],
                    'is_verified': customer['is_verified']
                }
            })
            
        except Exception as e:
            print(f"Customer login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    @app.route('/api/v1/customer/change-password', methods=['POST'])
    @jwt_required()
    def change_customer_password():
        """Change customer password"""
        try:
            customer_id = get_jwt_identity()
            data = request.get_json()
            
            current_password = data.get('current_password', '')
            new_password = data.get('new_password', '')
            
            if not current_password or not new_password:
                return jsonify({'error': 'Current and new passwords are required'}), 400
            
            if len(new_password) < 6:
                return jsonify({'error': 'New password must be at least 6 characters'}), 400
            
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get current password hash
            cursor.execute("SELECT password_hash FROM customers WHERE id = %s", (customer_id,))
            customer = cursor.fetchone()
            
            if not customer or not verify_password(current_password, customer['password_hash']):
                conn.close()
                return jsonify({'error': 'Current password is incorrect'}), 400
            
            # Update password
            new_password_hash = hash_password(new_password)
            cursor.execute(
                "UPDATE customers SET password_hash = %s, updated_at = %s WHERE id = %s",
                (new_password_hash, datetime.now(), customer_id)
            )
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Password changed successfully'})
            
        except Exception as e:
            print(f"Change password error: {e}")
            return jsonify({'error': 'Failed to change password'}), 500
    
    @app.route('/api/v1/customer/reset-password', methods=['POST'])
    def reset_customer_password():
        """Reset customer password via email/phone"""
        try:
            data = request.get_json()
            email_or_phone = data.get('email_or_phone', '').strip()
            
            if not email_or_phone:
                return jsonify({'error': 'Email or phone is required'}), 400
            
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Find customer
            cursor.execute(
                "SELECT id, email, phone FROM customers WHERE email = %s OR phone = %s",
                (email_or_phone, email_or_phone)
            )
            customer = cursor.fetchone()
            
            if not customer:
                conn.close()
                return jsonify({'error': 'Customer not found'}), 404
            
            # Generate new password
            new_password = generate_password()
            password_hash = hash_password(new_password)
            
            # Update password
            cursor.execute(
                "UPDATE customers SET password_hash = %s, updated_at = %s WHERE id = %s",
                (password_hash, datetime.now(), customer['id'])
            )
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'message': 'Password reset successful',
                'new_password': new_password,
                'note': 'New password sent to your registered email/phone'
            })
            
        except Exception as e:
            print(f"Reset password error: {e}")
            return jsonify({'error': 'Failed to reset password'}), 500