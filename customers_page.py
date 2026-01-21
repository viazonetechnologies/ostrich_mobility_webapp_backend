from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import pymysql
import re
from database import get_db, sanitize_input

def validate_customer_data(data):
    """Enhanced customer data validation"""
    errors = []
    
    # Required fields validation
    required_fields = {
        'customer_type': 'Customer type',
        'contact_person': 'Contact person',
        'email': 'Email',
        'phone': 'Phone number',
        'address': 'Address',
        'city': 'City',
        'state': 'State',
        'country': 'Country',
        'pin_code': 'PIN code'
    }
    
    for field, label in required_fields.items():
        if not data.get(field, '').strip():
            errors.append(f'{label} is required')
    
    # Contact person validation
    if data.get('contact_person'):
        contact_person = data['contact_person'].strip()
        if len(contact_person) < 2:
            errors.append('Contact person must be at least 2 characters')
        elif len(contact_person) > 100:
            errors.append('Contact person must be less than 100 characters')
        elif not re.match(r'^[a-zA-Z\s.&-]+$', contact_person):
            errors.append('Contact person can only contain letters, spaces, dots, ampersands, and hyphens')
    
    # Email validation
    if data.get('email'):
        email = data['email'].strip()
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append('Please enter a valid email address')
    
    # Phone validation (Indian mobile numbers)
    if data.get('phone'):
        phone = re.sub(r'[\s\-()]', '', data['phone'])
        if not re.match(r'^(\+91|91)?[6-9]\d{9}$', phone):
            errors.append('Please enter a valid Indian mobile number (10 digits starting with 6-9)')
    
    # Address validation
    if data.get('address') and len(data['address'].strip()) < 10:
        errors.append('Address must be at least 10 characters')
    
    # City validation
    if data.get('city'):
        city = data['city'].strip()
        if len(city) < 2:
            errors.append('City must be at least 2 characters')
        elif not re.match(r'^[a-zA-Z\s.-]+$', city):
            errors.append('City can only contain letters, spaces, dots, and hyphens')
    
    # State validation
    if data.get('state'):
        state = data['state'].strip()
        if len(state) < 2:
            errors.append('State must be at least 2 characters')
        elif not re.match(r'^[a-zA-Z\s.-]+$', state):
            errors.append('State can only contain letters, spaces, dots, and hyphens')
    
    # PIN code validation (6 digits)
    if data.get('pin_code'):
        pin_code = str(data['pin_code']).strip()
        if not re.match(r'^\d{6}$', pin_code):
            errors.append('PIN code must be exactly 6 digits')
    
    return errors

def register_customers_routes(app):
    """Register customer routes"""
    
    @app.route('/api/v1/customers/', methods=['GET'])
    @jwt_required()
    def get_customers():
        """Get all customers with search and filter"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get query parameters
            search = request.args.get('search', '').strip()
            customer_type = request.args.get('customer_type', '').strip() or request.args.get('type', '').strip()
            
            print(f"Search: '{search}', Type: '{customer_type}'")
            
            # Base query - include mobile registered customers
            query = """
                SELECT id, 
                       COALESCE(NULLIF(contact_person, ''), NULLIF(individual_name, ''), NULLIF(company_name, ''), 'Unknown') as name,
                       contact_person, individual_name, company_name, phone, email, address, city, state, 
                       created_at, customer_code, customer_type,
                       is_verified as verification_status, pin_code, 'India' as country, 
                       CASE 
                         WHEN registration_source = 'mobile_app' THEN 'mobile_app'
                         WHEN registration_source IS NULL OR registration_source = '' THEN 'web'
                         ELSE registration_source
                       END as registration_source, 
                       COALESCE(has_mobile_access, 0) as has_mobile_access
                FROM customers 
            """
            
            params = []
            conditions = []
            
            # Add search condition
            if search:
                search_term = f"%{search}%"
                conditions.append("""
                    (LOWER(contact_person) LIKE LOWER(%s) OR 
                     LOWER(individual_name) LIKE LOWER(%s) OR
                     LOWER(company_name) LIKE LOWER(%s) OR 
                     LOWER(email) LIKE LOWER(%s) OR 
                     phone LIKE %s OR 
                     LOWER(customer_code) LIKE LOWER(%s))
                """)
                params.extend([search_term] * 6)
            
            # Add type filter (handles both customer_type and registration_source)
            if customer_type and customer_type.lower() != 'all':
                if customer_type.lower() in ['mobile_app', 'web']:
                    conditions.append("LOWER(registration_source) = LOWER(%s)")
                    params.append(customer_type)
                else:
                    conditions.append("LOWER(customer_type) = LOWER(%s)")
                    params.append(customer_type)
            
            # Build final query
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT 200"
            
            cursor.execute(query, params)
            customers = cursor.fetchall()
            
            conn.close()
            return jsonify(customers)
            
        except Exception as e:
            print(f"Get customers error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/customers/', methods=['POST'])
    @jwt_required()
    def create_customer():
        """Create new customer with enhanced validation"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate data
            validation_errors = validate_customer_data(data)
            if validation_errors:
                return jsonify({'error': validation_errors[0]}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if phone already exists
            cursor.execute("SELECT id FROM customers WHERE phone = %s", (data.get('phone', '').strip(),))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Phone number already exists'}), 400
            
            # Check if email already exists
            cursor.execute("SELECT id FROM customers WHERE email = %s", (data.get('email', '').strip(),))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Email address already exists'}), 400
            
            # Generate customer code
            cursor.execute("SELECT MAX(CAST(SUBSTRING(customer_code, 5) AS UNSIGNED)) as max_num FROM customers WHERE customer_code LIKE 'CUST%'")
            result = cursor.fetchone()
            next_num = (result['max_num'] or 0) + 1 if result else 1
            customer_code = f"CUST{next_num:03d}"
            
            # Hash password if provided
            password_hash = None
            if data.get('password'):
                import hashlib
                password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
            
            # Insert customer
            query = """
                INSERT INTO customers (
                    customer_code, customer_type, individual_name, company_name, contact_person,
                    email, phone, password_hash, address, city, state, country, pin_code, 
                    registration_source, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                customer_code,
                sanitize_input(data.get('customer_type', 'B2C')),
                sanitize_input(data.get('name', '')),
                sanitize_input(data.get('name', '')),
                sanitize_input(data.get('contact_person', '')),
                sanitize_input(data.get('email', '')),
                sanitize_input(data.get('phone', '')),
                password_hash,
                sanitize_input(data.get('address', '')),
                sanitize_input(data.get('city', '')),
                sanitize_input(data.get('state', '')),
                sanitize_input(data.get('country', 'India')),
                sanitize_input(data.get('pin_code', '')),
                'web',
                datetime.now(),
                datetime.now()
            ))
            
            customer_id = cursor.lastrowid
            conn.commit()
            
            # Get created customer
            cursor.execute("""
                SELECT id, customer_code, customer_type, individual_name, company_name, 
                       contact_person, email, phone, address, city, state, country, pin_code,
                       registration_source, created_at
                FROM customers WHERE id = %s
            """, (customer_id,))
            customer = cursor.fetchone()
            
            conn.close()
            return jsonify(customer), 201
            
        except Exception as e:
            print(f"Create customer error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Failed to create customer'}), 500
    
    @app.route('/api/v1/customers/<int:customer_id>', methods=['PUT'])
    @jwt_required()
    def update_customer(customer_id):
        """Update existing customer"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate data
            validation_errors = validate_customer_data(data)
            if validation_errors:
                return jsonify({'error': validation_errors[0]}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if customer exists
            cursor.execute("SELECT id FROM customers WHERE id = %s", (customer_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Customer not found'}), 404
            
            # Check if phone already exists (excluding current customer)
            cursor.execute("SELECT id FROM customers WHERE phone = %s AND id != %s", 
                         (data.get('phone', '').strip(), customer_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Phone number already exists'}), 400
            
            # Check if email already exists (excluding current customer)
            cursor.execute("SELECT id FROM customers WHERE email = %s AND id != %s", 
                         (data.get('email', '').strip(), customer_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Email address already exists'}), 400
            
            # Update customer
            if data.get('password'):
                # Update with new password
                import hashlib
                password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
                query = """
                    UPDATE customers SET 
                        customer_type = %s, company_name = %s, individual_name = %s, 
                        contact_person = %s, email = %s, phone = %s, password_hash = %s, address = %s, 
                        city = %s, state = %s, country = %s, pin_code = %s, updated_at = %s
                    WHERE id = %s
                """
                cursor.execute(query, (
                    sanitize_input(data.get('customer_type', 'B2C')),
                    sanitize_input(data.get('name', '')),
                    sanitize_input(data.get('name', '')),
                    sanitize_input(data.get('contact_person', '')),
                    sanitize_input(data.get('email', '')),
                    sanitize_input(data.get('phone', '')),
                    password_hash,
                    sanitize_input(data.get('address', '')),
                    sanitize_input(data.get('city', '')),
                    sanitize_input(data.get('state', '')),
                    sanitize_input(data.get('country', 'India')),
                    sanitize_input(data.get('pin_code', '')),
                    datetime.now(),
                    customer_id
                ))
            else:
                # Update without changing password
                query = """
                    UPDATE customers SET 
                        customer_type = %s, company_name = %s, individual_name = %s, 
                        contact_person = %s, email = %s, phone = %s, address = %s, 
                        city = %s, state = %s, country = %s, pin_code = %s, updated_at = %s
                    WHERE id = %s
                """
                cursor.execute(query, (
                    sanitize_input(data.get('customer_type', 'B2C')),
                    sanitize_input(data.get('name', '')),
                    sanitize_input(data.get('name', '')),
                    sanitize_input(data.get('contact_person', '')),
                    sanitize_input(data.get('email', '')),
                    sanitize_input(data.get('phone', '')),
                    sanitize_input(data.get('address', '')),
                    sanitize_input(data.get('city', '')),
                    sanitize_input(data.get('state', '')),
                    sanitize_input(data.get('country', 'India')),
                    sanitize_input(data.get('pin_code', '')),
                    datetime.now(),
                    customer_id
                ))
            
            conn.commit()
            
            # Get updated customer
            cursor.execute("""
                SELECT id, customer_code, customer_type, individual_name, company_name, 
                       contact_person, email, phone, address, city, state, country, pin_code,
                       registration_source, created_at, updated_at
                FROM customers WHERE id = %s
            """, (customer_id,))
            customer = cursor.fetchone()
            
            conn.close()
            return jsonify(customer)
            
        except Exception as e:
            print(f"Update customer error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Failed to update customer'}), 500
    
    @app.route('/api/v1/customers/<int:customer_id>', methods=['DELETE'])
    @jwt_required()
    def delete_customer(customer_id):
        """Delete customer"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if customer exists
            cursor.execute("SELECT id FROM customers WHERE id = %s", (customer_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Customer not found'}), 404
            
            # Check for related records (sales, service tickets, etc.)
            cursor.execute("SELECT COUNT(*) as count FROM sales WHERE customer_id = %s", (customer_id,))
            sales_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM service_tickets WHERE customer_id = %s", (customer_id,))
            tickets_count = cursor.fetchone()['count']
            
            if sales_count > 0 or tickets_count > 0:
                conn.close()
                return jsonify({
                    'error': f'Cannot delete customer with existing records ({sales_count} sales, {tickets_count} service tickets)'
                }), 400
            
            # Delete customer
            cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Customer deleted successfully'})
            
        except Exception as e:
            print(f"Delete customer error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Failed to delete customer'}), 500
    
    @app.route('/api/v1/customers/test', methods=['GET'])
    def test_customers():
        """Test endpoint without JWT"""
        try:
            print("Testing customers endpoint...")
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            count_result = cursor.fetchone()
            
            cursor.execute("SELECT * FROM customers LIMIT 5")
            sample_customers = cursor.fetchall()
            
            conn.close()
            return jsonify({
                'total_count': count_result['count'],
                'sample_data': sample_customers
            })
            
        except Exception as e:
            print(f"Test customers error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)})