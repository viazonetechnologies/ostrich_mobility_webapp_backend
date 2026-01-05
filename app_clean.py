from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import secrets
from functools import wraps
import pymysql
import os
from contextlib import contextmanager

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=False, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])

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
        return jsonify({'error': 'Token required'}), 401
    return decorated

@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Aru247899!',
            database='ostrich_db',
            port=3306,
            charset='utf8mb4'
        )
        yield connection
    except Exception as e:
        print(f"Database connection failed: {e}")
        yield None
    finally:
        if connection:
            try:
                connection.close()
            except:
                pass

# Global OPTIONS handler for all routes
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# Health check
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

# Auth endpoints
@app.route('/api/v1/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    # Handle both form data and JSON data
    username = request.form.get('username') or (request.get_json(silent=True) or {}).get('username')
    password = request.form.get('password') or (request.get_json(silent=True) or {}).get('password')
    
    # Allow any login for testing
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
    
    return jsonify({"detail": "Invalid credentials"}), 401

# Customers endpoints
@app.route('/api/v1/customers/', methods=['GET'])
@token_required
def read_customers(current_user):
    try:
        with get_db_connection() as conn:
            if conn is None:
                return jsonify([])
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers LIMIT 100")
            customers_db = cursor.fetchall()
            
            result = []
            for customer in customers_db:
                result.append({
                    "id": customer[0],
                    "customer_code": customer[1] if len(customer) > 1 else f"CUS{customer[0]:06d}",
                    "customer_type": customer[2] if len(customer) > 2 else "b2c",
                    "company_name": customer[3] if len(customer) > 3 else "",
                    "contact_person": customer[4] if len(customer) > 4 else "",
                    "email": customer[5] if len(customer) > 5 else "",
                    "phone": customer[6] if len(customer) > 6 else "",
                    "address": customer[7] if len(customer) > 7 else "",
                    "city": customer[8] if len(customer) > 8 else "",
                    "state": customer[9] if len(customer) > 9 else "",
                    "country": customer[10] if len(customer) > 10 else "India",
                    "pin_code": customer[11] if len(customer) > 11 else "",
                    "status": 'active',
                    "created_at": str(customer[-1]) if len(customer) > 12 else None
                })
            return jsonify(result)
    except Exception as e:
        print(f"Database error in customers: {e}")
        return jsonify([])

@app.route('/api/v1/customers/', methods=['POST'])
@token_required
def create_customer(current_user):
    data = request.get_json()
    try:
        with get_db_connection() as conn:
            if conn is None:
                return jsonify({"message": "Database connection failed"}), 500
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (customer_code, customer_type, company_name, contact_person, 
                                     email, phone, address, city, state, country, pin_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('customer_code', f"CUS{int(datetime.now().timestamp())}"),
                data.get('customer_type', 'b2c'),
                data.get('company_name', ''),
                data.get('contact_person', ''),
                data.get('email', ''),
                data.get('phone', ''),
                data.get('address', ''),
                data.get('city', ''),
                data.get('state', ''),
                data.get('country', 'India'),
                data.get('pin_code', '')
            ))
            conn.commit()
            new_id = cursor.lastrowid
            return jsonify({"id": new_id, "message": "Customer created successfully"})
    except Exception as e:
        print(f"Database error in create_customer: {e}")
        return jsonify({"message": "Failed to create customer"}), 500

# Services endpoints
@app.route('/api/v1/services/', methods=['GET'])
@token_required
def read_services(current_user):
    try:
        with get_db_connection() as conn:
            if conn is None:
                return jsonify([{
                    "id": 1,
                    "ticket_number": "TKT000001",
                    "customer_id": 1,
                    "customer_name": "Tech Solutions Ltd",
                    "product_serial_number": "OST-3HP-001",
                    "issue_description": "Motor not starting properly",
                    "priority": "HIGH",
                    "status": "OPEN",
                    "assigned_staff_id": 1,
                    "assigned_staff_name": "Service Engineer",
                    "scheduled_date": "2025-12-31",
                    "completed_date": None,
                    "service_notes": "Initial inspection required",
                    "customer_feedback": None,
                    "rating": None,
                    "created_at": "2025-12-30T10:00:00"
                }])
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT st.*, c.company_name, c.contact_person
                FROM service_tickets st
                LEFT JOIN customers c ON st.customer_id = c.id
                ORDER BY st.id DESC
                LIMIT 100
            """)
            services_db = cursor.fetchall()
            
            result = []
            for service in services_db:
                customer_name = (service[15] if len(service) > 15 else None) or (service[16] if len(service) > 16 else None) or f"ID: {service[2]}"
                
                result.append({
                    "id": service[0],
                    "ticket_number": service[1] if len(service) > 1 else f"TKT{service[0]:06d}",
                    "customer_id": service[2] if len(service) > 2 else None,
                    "customer_name": customer_name,
                    "product_serial_number": service[3] if len(service) > 3 else "",
                    "issue_description": service[4] if len(service) > 4 else "",
                    "priority": service[5] if len(service) > 5 else "MEDIUM",
                    "status": service[6] if len(service) > 6 else "OPEN",
                    "assigned_staff_id": service[7] if len(service) > 7 else None,
                    "assigned_staff_name": "Service Engineer",
                    "scheduled_date": str(service[8]) if len(service) > 8 and service[8] else None,
                    "completed_date": str(service[9]) if len(service) > 9 and service[9] else None,
                    "service_notes": service[10] if len(service) > 10 else "",
                    "customer_feedback": service[11] if len(service) > 11 else None,
                    "rating": service[12] if len(service) > 12 else None,
                    "created_at": str(service[13]) if len(service) > 13 and service[13] else None
                })
            return jsonify(result)
    except Exception as e:
        print(f"Database error in services: {e}")
        return jsonify([])

# Enquiries endpoints
@app.route('/api/v1/enquiries/', methods=['GET'])
@token_required
def read_enquiries(current_user):
    try:
        with get_db_connection() as conn:
            if conn is None:
                return jsonify([{
                    "id": 1,
                    "enquiry_number": "ENQ000001",
                    "customer_id": 1,
                    "customer_name": "Tech Solutions Ltd",
                    "product_id": 1,
                    "product_name": "3HP Single Phase Motor",
                    "quantity": 5,
                    "message": "Need bulk pricing for 5 units",
                    "status": "open",
                    "assigned_to": 1,
                    "assigned_name": "Sales Manager",
                    "follow_up_date": "2025-12-31",
                    "notes": "High priority customer",
                    "created_at": "2025-12-30T09:00:00"
                }])
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, c.company_name, c.contact_person, p.name as product_name
                FROM enquiries e
                LEFT JOIN customers c ON e.customer_id = c.id
                LEFT JOIN products p ON e.product_id = p.id
                ORDER BY e.id DESC
                LIMIT 100
            """)
            enquiries_db = cursor.fetchall()
            
            result = []
            for enquiry in enquiries_db:
                customer_name = (enquiry[11] if len(enquiry) > 11 else None) or (enquiry[12] if len(enquiry) > 12 else None) or f"ID: {enquiry[2]}"
                product_name = (enquiry[13] if len(enquiry) > 13 else None) or f"ID: {enquiry[3]}"
                
                result.append({
                    "id": enquiry[0],
                    "enquiry_number": enquiry[1] if len(enquiry) > 1 else f"ENQ{enquiry[0]:06d}",
                    "customer_id": enquiry[2] if len(enquiry) > 2 else None,
                    "customer_name": customer_name,
                    "product_id": enquiry[3] if len(enquiry) > 3 else None,
                    "product_name": product_name,
                    "quantity": enquiry[4] if len(enquiry) > 4 else 1,
                    "message": enquiry[5] if len(enquiry) > 5 else "",
                    "status": enquiry[6] if len(enquiry) > 6 else "open",
                    "assigned_to": enquiry[7] if len(enquiry) > 7 else None,
                    "assigned_name": "Sales Manager",
                    "follow_up_date": str(enquiry[8]) if len(enquiry) > 8 and enquiry[8] else None,
                    "notes": enquiry[9] if len(enquiry) > 9 else "",
                    "created_at": str(enquiry[10]) if len(enquiry) > 10 and enquiry[10] else None
                })
            return jsonify(result)
    except Exception as e:
        print(f"Database error in enquiries: {e}")
        return jsonify([])

# Notifications endpoints
@app.route('/api/v1/notifications/unread-count', methods=['GET'])
@token_required
def get_unread_notifications_count(current_user):
    try:
        with get_db_connection() as conn:
            if conn is None:
                return jsonify({"unread_count": 3})
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0")
            count = cursor.fetchone()[0]
            return jsonify({"unread_count": count})
    except Exception as e:
        print(f"Database error in unread notifications count: {e}")
        return jsonify({"unread_count": 0})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)