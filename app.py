from flask import jsonify, request
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql
from local_image_service import local_image_service

def register_product_images_routes(app):
    @app.route('/api/v1/product-images/', methods=['GET'])
    @jwt_required()
    def get_product_images():
        """Get all product images with product details"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT p.id, p.name, p.product_code, p.image_url,
                       c.name as category_name, p.price, p.stock_quantity,
                       p.created_at, p.updated_at
                FROM products p
                LEFT JOIN product_categories c ON p.category_id = c.id
                WHERE p.image_url IS NOT NULL AND p.image_url != ''
                ORDER BY p.updated_at DESC
            """
            
            cursor.execute(query)
            products = cursor.fetchall()
            conn.close()
            
            return jsonify(products)
            
        except Exception as e:
            print(f"Get product images error: {e}")
            return jsonify([])
    
    # Removed conflicting paginated route that conflicts with product_id route
    
    @app.route('/api/v1/product-images/sync-existing', methods=['POST'])
    @jwt_required()
    def sync_existing_images():
        """Sync existing product images - disabled to prevent hardcoded data"""
        return jsonify({
            'message': 'Sync disabled to prevent hardcoded placeholder images',
            'updated_count': 0
        })
    
    @app.route('/api/v1/product-images/missing', methods=['GET'])
    @jwt_required()
    def get_products_without_images():
        """Get products that don't have images"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT p.id, p.name, p.product_code, 
                       c.name as category_name, p.price, p.stock_quantity
                FROM products p
                LEFT JOIN product_categories c ON p.category_id = c.id
                WHERE p.image_url IS NULL OR p.image_url = ''
                ORDER BY p.name
            """
            
            cursor.execute(query)
            products = cursor.fetchall()
            conn.close()
            
            return jsonify(products)
            
        except Exception as e:
            print(f"Get products without images error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/product-images/stats', methods=['GET'])
    @jwt_required()
    def get_image_stats():
        """Get product image statistics"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Total products
            cursor.execute("SELECT COUNT(*) as total FROM products")
            total = cursor.fetchone()['total']
            
            # Products with images
            cursor.execute("SELECT COUNT(*) as with_images FROM products WHERE image_url IS NOT NULL AND image_url != ''")
            with_images = cursor.fetchone()['with_images']
            
            # Products without images
            without_images = total - with_images
            
            # Percentage
            percentage = (with_images / total * 100) if total > 0 else 0
            
            conn.close()
            
            return jsonify({
                'total_products': total,
                'with_images': with_images,
                'without_images': without_images,
                'percentage_complete': round(percentage, 1)
            })
            
        except Exception as e:
            print(f"Get image stats error: {e}")
            return jsonify({})
    
    @app.route('/api/v1/product-images/debug/<int:product_id>', methods=['POST'])
    def debug_upload(product_id):
        """Debug endpoint to check request data"""
        try:
            print(f"Debug upload for product {product_id}")
            print(f"Request files: {list(request.files.keys())}")
            print(f"Request form: {dict(request.form)}")
            
            return jsonify({
                'product_id': product_id,
                'files': list(request.files.keys()),
                'form': dict(request.form)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/product-images/check/<int:product_id>', methods=['GET'])
    def check_product_image(product_id):
        """Check if product has image in database"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT id, name, image_url FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            conn.close()
            
            return jsonify(product if product else {'error': 'Product not found'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

def register_enquiries_routes(app):
    @app.route('/api/v1/enquiries/', methods=['GET', 'POST'])
    def handle_enquiries():
        print("DEBUG: handle_enquiries called with updated code - v2")  # Debug line
        if request.method == 'GET':
            try:
                print("DEBUG: Executing GET enquiries with new SQL query")  # Debug line
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT e.*, 
                           COALESCE(
                               NULLIF(c.contact_person, ''), 
                               NULLIF(c.individual_name, ''), 
                               NULLIF(c.company_name, '')
                           ) as customer_name, 
                           c.email, c.phone, 
                           p.name as product_name,
                           COALESCE(e.quantity, 1) as quantity
                    FROM enquiries e
                    LEFT JOIN customers c ON e.customer_id = c.id
                    LEFT JOIN products p ON e.product_id = p.id
                    ORDER BY e.created_at DESC
                """)
                enquiries = cursor.fetchall()
                print(f"DEBUG: Found {len(enquiries)} enquiries")  # Debug line
                if enquiries:
                    print(f"DEBUG: First enquiry keys: {list(enquiries[0].keys())}")  # Debug line
                conn.close()
                
                # Ensure all fields are safe (no null values)
                safe_enquiries = []
                for enquiry in enquiries:
                    safe_enquiry = {}
                    for key, value in enquiry.items():
                        if key == 'status' and (value is None or value == ''):
                            safe_enquiry[key] = 'NEW'  # Default status
                        elif value is None:
                            safe_enquiry[key] = ''
                        else:
                            safe_enquiry[key] = value
                    safe_enquiries.append(safe_enquiry)
                
                return jsonify(safe_enquiries)
                
            except Exception as e:
                print(f"Get enquiries error: {e}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Generate unique enquiry number
                cursor.execute("SELECT enquiry_number FROM enquiries ORDER BY id DESC LIMIT 1")
                last_enquiry = cursor.fetchone()
                if last_enquiry and last_enquiry['enquiry_number']:
                    # Extract number from last enquiry (e.g., ENQ000016 -> 16)
                    last_num = int(last_enquiry['enquiry_number'][3:])
                    enquiry_number = f"ENQ{str(last_num + 1).zfill(6)}"
                else:
                    enquiry_number = "ENQ000001"
                
                # Process follow_up_date
                follow_up_date = data.get('follow_up_date')
                if follow_up_date:
                    # Convert from frontend format (YYYY-MM-DD) to MySQL format
                    if 'T' in follow_up_date:
                        follow_up_date = follow_up_date.split('T')[0]
                    # Ensure it's in YYYY-MM-DD format
                    try:
                        from datetime import datetime
                        datetime.strptime(follow_up_date, '%Y-%m-%d')
                    except:
                        follow_up_date = None
                else:
                    follow_up_date = None
                
                # Insert enquiry
                cursor.execute("""
                    INSERT INTO enquiries (enquiry_number, customer_id, product_id, quantity, message, status, assigned_to, follow_up_date, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    enquiry_number,
                    data.get('customer_id'),
                    data.get('product_id'),
                    data.get('quantity', 1),
                    data.get('message', ''),
                    data.get('status', 'NEW'),
                    data.get('assigned_to'),
                    follow_up_date,
                    data.get('notes', '')
                ))
                
                conn.commit()
                enquiry_id = cursor.lastrowid
                
                # Create notification for admin
                cursor.execute("""
                    INSERT INTO notifications (user_id, title, message, type, customer_id, is_read, is_sent)
                    VALUES (1, %s, %s, 'INFO', %s, 0, 0)
                """, (
                    f'New Enquiry: {enquiry_number}',
                    f'New enquiry received from customer regarding {data.get("message", "product inquiry")}',
                    data.get('customer_id')
                ))
                conn.commit()
                
                conn.close()
                
                return jsonify({
                    'id': enquiry_id,
                    'enquiry_number': enquiry_number,
                    'message': 'Enquiry created successfully'
                }), 201
                
            except Exception as e:
                print(f"Create enquiry error: {e}")
                return jsonify({'error': f'Failed to create enquiry: {str(e)}'}), 500
    
    @app.route('/api/v1/enquiries/<int:enquiry_id>', methods=['GET', 'PUT', 'DELETE'])
    def handle_single_enquiry(enquiry_id):
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT e.*, 
                           COALESCE(
                               NULLIF(c.contact_person, ''), 
                               NULLIF(c.individual_name, ''), 
                               NULLIF(c.company_name, '')
                           ) as customer_name, 
                           c.email, c.phone, 
                           p.name as product_name,
                           COALESCE(e.quantity, 1) as quantity
                    FROM enquiries e
                    LEFT JOIN customers c ON e.customer_id = c.id
                    LEFT JOIN products p ON e.product_id = p.id
                    WHERE e.id = %s
                """, (enquiry_id,))
                enquiry = cursor.fetchone()
                conn.close()
                
                if not enquiry:
                    return jsonify({'error': 'Enquiry not found'}), 404
                
                # Handle null values
                for key, value in enquiry.items():
                    if key == 'status' and (value is None or value == ''):
                        enquiry[key] = 'NEW'
                    elif value is None:
                        enquiry[key] = ''
                
                return jsonify(enquiry)
                
            except Exception as e:
                print(f"Get enquiry error: {e}")
                return jsonify({'error': 'Failed to fetch enquiry'}), 500
        
        elif request.method == 'PUT':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Process follow_up_date
                follow_up_date = data.get('follow_up_date')
                if follow_up_date:
                    # Convert from frontend format to MySQL format
                    if 'T' in follow_up_date:
                        follow_up_date = follow_up_date.split('T')[0]
                    # Ensure it's in YYYY-MM-DD format
                    try:
                        from datetime import datetime
                        datetime.strptime(follow_up_date, '%Y-%m-%d')
                    except:
                        follow_up_date = None
                else:
                    follow_up_date = None
                
                # Update enquiry
                cursor.execute("""
                    UPDATE enquiries SET 
                        customer_id = %s, product_id = %s, quantity = %s, message = %s, 
                        status = %s, assigned_to = %s, follow_up_date = %s, notes = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    data.get('customer_id'),
                    data.get('product_id'),
                    data.get('quantity', 1),
                    data.get('message', ''),
                    data.get('status', 'NEW'),
                    data.get('assigned_to'),
                    follow_up_date,
                    data.get('notes', ''),
                    enquiry_id
                ))
                                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'Enquiry not found'}), 404
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Enquiry updated successfully'})
                
            except Exception as e:
                print(f"Update enquiry error: {e}")
                return jsonify({'error': f'Failed to update enquiry: {str(e)}'}), 500
        
        elif request.method == 'DELETE':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Delete enquiry
                cursor.execute("DELETE FROM enquiries WHERE id = %s", (enquiry_id,))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'Enquiry not found'}), 404
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Enquiry deleted successfully'})
                
            except Exception as e:
                print(f"Delete enquiry error: {e}")
                return jsonify({'error': f'Failed to delete enquiry: {str(e)}'}), 500

def register_service_routes(app):
    @app.route('/api/v1/services/', methods=['GET', 'POST'])
    def handle_service_tickets():
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT st.*, 
                           COALESCE(
                               NULLIF(c.contact_person, ''), 
                               NULLIF(c.individual_name, ''), 
                               NULLIF(c.company_name, '')
                           ) as customer_name, 
                           c.email, c.phone, 
                           p.name as product_name
                    FROM service_tickets st
                    LEFT JOIN customers c ON st.customer_id = c.id
                    LEFT JOIN products p ON st.product_id = p.id
                    ORDER BY st.created_at DESC
                """)
                tickets = cursor.fetchall()
                conn.close()
                
                # Ensure all fields are safe
                safe_tickets = []
                for ticket in tickets:
                    safe_ticket = {}
                    for key, value in ticket.items():
                        if key == 'status' and (value is None or value == ''):
                            safe_ticket[key] = 'OPEN'
                        elif value is None:
                            safe_ticket[key] = ''
                        else:
                            safe_ticket[key] = value
                    safe_tickets.append(safe_ticket)
                
                return jsonify(safe_tickets)
                
            except Exception as e:
                print(f"Get service tickets error: {e}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Generate ticket number
                cursor.execute("SELECT ticket_number FROM service_tickets ORDER BY id DESC LIMIT 1")
                last_ticket = cursor.fetchone()
                if last_ticket and last_ticket['ticket_number']:
                    last_num = int(last_ticket['ticket_number'][3:])
                    ticket_number = f"SRV{str(last_num + 1).zfill(6)}"
                else:
                    ticket_number = "SRV000001"
                
                # Insert service ticket
                cursor.execute("""
                    INSERT INTO service_tickets (ticket_number, customer_id, product_id, issue_description, priority, status, assigned_staff_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticket_number,
                    data.get('customer_id'),
                    data.get('product_id'),
                    data.get('issue_description', ''),
                    data.get('priority', 'MEDIUM'),
                    data.get('status', 'OPEN'),
                    data.get('assigned_to')
                ))
                
                conn.commit()
                ticket_id = cursor.lastrowid
                
                # Create notification for admin
                cursor.execute("""
                    INSERT INTO notifications (user_id, title, message, type, customer_id, is_read, is_sent)
                    VALUES (1, %s, %s, 'WARNING', %s, 0, 0)
                """, (
                    f'New Service Ticket: {ticket_number}',
                    f'New service ticket created: {data.get("issue_description", "Service request")}',
                    data.get('customer_id')
                ))
                conn.commit()
                
                conn.close()
                
                return jsonify({
                    'id': ticket_id,
                    'ticket_number': ticket_number,
                    'message': 'Service ticket created successfully'
                }), 201
                
            except Exception as e:
                print(f"Create service ticket error: {e}")
                return jsonify({'error': f'Failed to create service ticket: {str(e)}'}), 500
    
    @app.route('/api/v1/services/<int:ticket_id>', methods=['GET', 'PUT', 'DELETE'])
    def handle_single_service_ticket(ticket_id):
        if request.method == 'PUT':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                cursor.execute("""
                    UPDATE service_tickets SET 
                        issue_description = %s, 
                        priority = %s, status = %s, assigned_staff_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    data.get('issue_description', ''),
                    data.get('priority', 'MEDIUM'),
                    data.get('status', 'OPEN'),
                    data.get('assigned_to'),
                    ticket_id
                ))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'Service ticket not found'}), 404
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Service ticket updated successfully'})
                
            except Exception as e:
                print(f"Update service ticket error: {e}")
                return jsonify({'error': f'Failed to update service ticket: {str(e)}'}), 500
        
        elif request.method == 'DELETE':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                cursor.execute("DELETE FROM service_tickets WHERE id = %s", (ticket_id,))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'Service ticket not found'}), 404
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Service ticket deleted successfully'})
                
            except Exception as e:
                print(f"Delete service ticket error: {e}")
                return jsonify({'error': f'Failed to delete service ticket: {str(e)}'}), 500

def register_sales_routes(app):
    @app.route('/api/v1/sales/', methods=['GET', 'POST'])
    def handle_sales():
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT s.*, 
                           COALESCE(
                               NULLIF(c.contact_person, ''), 
                               NULLIF(c.individual_name, ''), 
                               NULLIF(c.company_name, '')
                           ) as customer_name,
                           c.contact_person, c.email, c.phone,
                           CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, '')) as sold_by_name
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    LEFT JOIN users u ON s.created_by = u.id
                    ORDER BY s.sale_date DESC
                """)
                sales = cursor.fetchall()
                
                # Get items for each sale
                for sale in sales:
                    cursor.execute("""
                        SELECT si.*, p.name as product_name
                        FROM sale_items si
                        LEFT JOIN products p ON si.product_id = p.id
                        WHERE si.sale_id = %s
                    """, (sale['id'],))
                    sale['items'] = cursor.fetchall()
                
                conn.close()
                
                return jsonify(sales)
                
            except Exception as e:
                print(f"Get sales error: {e}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                print(f"DEBUG: customer_id={data.get('customer_id')}, type={type(data.get('customer_id'))}")
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Convert customer_code to customer_id if needed
                customer_value = data.get('customer_id')
                print(f"DEBUG: customer_value={customer_value}, isdigit={customer_value.isdigit() if isinstance(customer_value, str) else 'N/A'}")
                if isinstance(customer_value, str) and not customer_value.isdigit():
                    # It's a customer code, look up the ID
                    cursor.execute("SELECT id FROM customers WHERE customer_code = %s", (customer_value,))
                    customer_row = cursor.fetchone()
                    if customer_row:
                        customer_id = customer_row['id']
                    else:
                        conn.close()
                        return jsonify({'error': f'Customer with code {customer_value} not found'}), 400
                elif isinstance(customer_value, int):
                    customer_id = customer_value
                else:
                    customer_id = int(customer_value)
                
                # Generate sale number
                cursor.execute("SELECT sale_number FROM sales WHERE sale_number LIKE 'SAL%' ORDER BY id DESC LIMIT 1")
                last_sale = cursor.fetchone()
                if last_sale and last_sale['sale_number']:
                    try:
                        last_num = int(last_sale['sale_number'][3:])
                        sale_number = f"SAL{str(last_num + 1).zfill(6)}"
                    except (ValueError, IndexError):
                        sale_number = "SAL000001"
                else:
                    sale_number = "SAL000001"
                
                # Insert sale
                cursor.execute("""
                    INSERT INTO sales (sale_number, customer_id, created_by, sale_date, total_amount, 
                                     discount_percentage, discount_amount, final_amount, 
                                     payment_status, delivery_status, delivery_date, 
                                     delivery_address, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    sale_number,
                    customer_id,
                    data.get('sales_executive_id'),
                    data.get('sale_date'),
                    float(data.get('total_amount')),
                    float(data.get('discount_percentage', 0)),
                    float(data.get('discount_amount', 0)),
                    float(data.get('final_amount')),
                    data.get('payment_status', 'pending'),
                    data.get('delivery_status', 'pending'),
                    data.get('delivery_date'),
                    data.get('delivery_address'),
                    data.get('notes')
                ))
                
                sale_id = cursor.lastrowid
                
                # Insert sale items
                if 'items' in data and data['items']:
                    for item in data['items']:
                        print(f"DEBUG: Processing item: {item}")
                        total_price = float(item.get('quantity', 0)) * float(item.get('unit_price', 0))
                        cursor.execute("""
                            INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            sale_id,
                            int(item.get('product_id')),
                            int(item.get('quantity')),
                            float(item.get('unit_price')),
                            total_price
                        ))
                
                conn.commit()
                conn.close()
                
                return jsonify({
                    'id': sale_id,
                    'sale_number': sale_number,
                    'message': 'Sale created successfully'
                }), 201
                
            except Exception as e:
                import traceback
                print(f"Create sale error: {e}")
                print(f"Full traceback: {traceback.format_exc()}")
                return jsonify({'error': f'Failed to create sale: {str(e)}'}), 500
    
    @app.route('/api/v1/sales/<int:sale_id>', methods=['GET', 'PUT', 'DELETE'])
    def handle_single_sale(sale_id):
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Get sale with items
                cursor.execute("""
                    SELECT s.*, 
                           COALESCE(
                               NULLIF(c.contact_person, ''), 
                               NULLIF(c.individual_name, ''), 
                               NULLIF(c.company_name, '')
                           ) as customer_name,
                           c.contact_person, c.email, c.phone,
                           CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, '')) as sold_by_name
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    LEFT JOIN users u ON s.created_by = u.id
                    WHERE s.id = %s
                """, (sale_id,))
                sale = cursor.fetchone()
                
                if not sale:
                    conn.close()
                    return jsonify({'error': 'Sale not found'}), 404
                
                # Get sale items
                cursor.execute("""
                    SELECT si.*, p.name as product_name
                    FROM sale_items si
                    LEFT JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = %s
                """, (sale_id,))
                items = cursor.fetchall()
                
                sale['items'] = items
                conn.close()
                
                return jsonify(sale)
                
            except Exception as e:
                print(f"Get sale error: {e}")
                return jsonify({'error': 'Failed to fetch sale'}), 500
        
        elif request.method == 'PUT':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Check current delivery status
                cursor.execute("SELECT delivery_status FROM sales WHERE id = %s", (sale_id,))
                sale = cursor.fetchone()
                if not sale:
                    conn.close()
                    return jsonify({'error': 'Sale not found'}), 404
                
                current_delivery_status = sale['delivery_status']
                
                # If delivery status is not pending, only allow payment_status update
                if current_delivery_status != 'pending':
                    cursor.execute("""
                        UPDATE sales SET 
                            payment_status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (data.get('payment_status', 'pending'), sale_id))
                    conn.commit()
                    conn.close()
                    return jsonify({'message': 'Payment status updated successfully'})
                
                # Convert customer_code to customer_id if needed
                customer_value = data.get('customer_id')
                if customer_value and isinstance(customer_value, str) and not customer_value.isdigit():
                    cursor.execute("SELECT id FROM customers WHERE customer_code = %s", (customer_value,))
                    customer_row = cursor.fetchone()
                    if customer_row:
                        customer_id = customer_row['id']
                    else:
                        conn.close()
                        return jsonify({'error': f'Customer with code {customer_value} not found'}), 400
                else:
                    customer_id = int(customer_value)
                
                # Update sale
                cursor.execute("""
                    UPDATE sales SET 
                        customer_id = %s, created_by = %s, sale_date = %s, total_amount = %s,
                        discount_percentage = %s, discount_amount = %s, final_amount = %s,
                        payment_status = %s, delivery_status = %s, delivery_date = %s,
                        delivery_address = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    customer_id,
                    data.get('sales_executive_id'),
                    data.get('sale_date'),
                    float(data.get('total_amount')),
                    float(data.get('discount_percentage', 0)),
                    float(data.get('discount_amount', 0)),
                    float(data.get('final_amount')),
                    data.get('payment_status', 'pending'),
                    data.get('delivery_status', 'pending'),
                    data.get('delivery_date'),
                    data.get('delivery_address'),
                    data.get('notes'),
                    sale_id
                ))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'Sale not found'}), 404
                
                # Update sale items - delete existing and insert new
                cursor.execute("DELETE FROM sale_items WHERE sale_id = %s", (sale_id,))
                
                if 'items' in data and data['items']:
                    for item in data['items']:
                        total_price = float(item.get('quantity', 0)) * float(item.get('unit_price', 0))
                        cursor.execute("""
                            INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            sale_id,
                            int(item.get('product_id')),
                            int(item.get('quantity')),
                            float(item.get('unit_price')),
                            total_price
                        ))
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Sale updated successfully'})
                
            except Exception as e:
                print(f"Update sale error: {e}")
                return jsonify({'error': f'Failed to update sale: {str(e)}'}), 500
        
        elif request.method == 'DELETE':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Check if sale has been dispatched
                cursor.execute("""
                    SELECT COUNT(*) as dispatch_count 
                    FROM dispatches 
                    WHERE sale_id = %s AND status IN ('in_transit', 'delivered')
                """, (sale_id,))
                result = cursor.fetchone()
                if result and result['dispatch_count'] > 0:
                    conn.close()
                    return jsonify({'error': 'Cannot delete sale that has been dispatched'}), 400
                
                # Delete sale items first
                cursor.execute("DELETE FROM sale_items WHERE sale_id = %s", (sale_id,))
                
                # Delete sale
                cursor.execute("DELETE FROM sales WHERE id = %s", (sale_id,))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'Sale not found'}), 404
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Sale deleted successfully'})
                
            except Exception as e:
                print(f"Delete sale error: {e}")
                return jsonify({'error': f'Failed to delete sale: {str(e)}'}), 500

def register_dispatch_routes(app):
    @app.route('/api/v1/dispatch/', methods=['GET', 'POST'])
    def handle_dispatch():
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT d.*, 
                           COALESCE(
                               NULLIF(c.contact_person, ''), 
                               NULLIF(c.individual_name, ''), 
                               NULLIF(c.company_name, '')
                           ) as customer_name,
                           GROUP_CONCAT(DISTINCT p.name SEPARATOR ', ') as product_name
                    FROM dispatches d
                    LEFT JOIN customers c ON d.customer_id = c.id
                    LEFT JOIN sale_items si ON d.sale_id = si.sale_id
                    LEFT JOIN products p ON si.product_id = p.id
                    GROUP BY d.id
                    ORDER BY d.dispatch_date DESC
                """)
                dispatches = cursor.fetchall()
                conn.close()
                
                return jsonify(dispatches)
                
            except Exception as e:
                print(f"Get dispatch error: {e}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                # Validate required fields
                required_fields = ['customer_id', 'sales_id', 'driver_name', 'driver_phone', 
                                 'vehicle_number', 'dispatch_date', 'estimated_delivery']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
                
                # Validate phone number format (basic)
                phone = str(data.get('driver_phone', '')).strip()
                if len(phone) < 10:
                    return jsonify({'error': 'Driver phone must be at least 10 digits'}), 400
                
                # Validate dates
                from datetime import datetime
                try:
                    dispatch_date = datetime.fromisoformat(data['dispatch_date'].replace('Z', ''))
                    estimated_delivery = datetime.fromisoformat(data['estimated_delivery'].replace('Z', ''))
                    
                    if estimated_delivery <= dispatch_date:
                        return jsonify({'error': 'Estimated delivery must be after dispatch date'}), 400
                except ValueError:
                    return jsonify({'error': 'Invalid date format'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Verify customer exists
                cursor.execute("SELECT id FROM customers WHERE id = %s", (data['customer_id'],))
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'Customer not found'}), 404
                
                # Verify sale exists
                cursor.execute("SELECT id FROM sales WHERE id = %s", (data['sales_id'],))
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'Sale not found'}), 404
                
                # Generate dispatch number
                cursor.execute("SELECT dispatch_number FROM dispatches ORDER BY id DESC LIMIT 1")
                last_dispatch = cursor.fetchone()
                if last_dispatch and last_dispatch['dispatch_number']:
                    last_num = int(last_dispatch['dispatch_number'][4:])
                    dispatch_number = f"DISP{str(last_num + 1).zfill(5)}"
                else:
                    dispatch_number = "DISP00001"
                
                cursor.execute("""
                    INSERT INTO dispatches (dispatch_number, sale_id, customer_id, product_id, driver_name, 
                                        driver_phone, vehicle_number, dispatch_date, 
                                        estimated_delivery, tracking_notes, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    dispatch_number,
                    data.get('sales_id'),
                    data.get('customer_id'),
                    None,
                    data.get('driver_name'),
                    phone,
                    data.get('vehicle_number'),
                    data.get('dispatch_date'),
                    data.get('estimated_delivery'),
                    data.get('tracking_notes', ''),
                    'pending'
                ))
                
                # Update sale status to processing when dispatch is created
                cursor.execute("""
                    UPDATE sales SET delivery_status = 'processing' WHERE id = %s
                """, (data.get('sales_id'),))
                
                conn.commit()
                dispatch_id = cursor.lastrowid
                conn.close()
                
                return jsonify({
                    'id': dispatch_id,
                    'dispatch_number': dispatch_number,
                    'message': 'Dispatch created successfully'
                }), 201
                
            except Exception as e:
                print(f"Create dispatch error: {e}")
                return jsonify({'error': f'Failed to create dispatch: {str(e)}'}), 500
    
    @app.route('/api/v1/dispatch/<int:dispatch_id>', methods=['PUT', 'DELETE'])
    def handle_single_dispatch(dispatch_id):
        if request.method == 'PUT':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Get dispatch info before update
                cursor.execute("SELECT customer_id, product_id, status FROM dispatches WHERE id = %s", (dispatch_id,))
                dispatch = cursor.fetchone()
                
                if not dispatch:
                    conn.close()
                    return jsonify({'error': 'Dispatch not found'}), 404
                
                # Convert datetime strings to MySQL format
                from datetime import datetime
                def convert_to_mysql_datetime(date_str):
                    if not date_str:
                        return None
                    try:
                        # Try parsing GMT format
                        dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            # Try ISO format
                            dt = datetime.fromisoformat(date_str.replace('Z', ''))
                            return dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            return date_str
                
                dispatch_date = convert_to_mysql_datetime(data.get('dispatch_date'))
                estimated_delivery = convert_to_mysql_datetime(data.get('estimated_delivery'))
                actual_delivery = convert_to_mysql_datetime(data.get('actual_delivery'))
                
                # Update dispatch
                cursor.execute("""
                    UPDATE dispatches SET 
                        driver_name = %s, driver_phone = %s, vehicle_number = %s,
                        dispatch_date = %s, estimated_delivery = %s, 
                        tracking_notes = %s, status = %s, actual_delivery = %s
                    WHERE id = %s
                """, (
                    data.get('driver_name'),
                    data.get('driver_phone'),
                    data.get('vehicle_number'),
                    dispatch_date,
                    estimated_delivery,
                    data.get('tracking_notes', ''),
                    data.get('status', 'pending'),
                    actual_delivery,
                    dispatch_id
                ))
                
                # Update sale delivery_status based on dispatch status
                new_status = data.get('status', 'pending')
                cursor.execute("SELECT sale_id FROM dispatches WHERE id = %s", (dispatch_id,))
                dispatch_info = cursor.fetchone()
                
                if dispatch_info and dispatch_info['sale_id']:
                    sale_id = dispatch_info['sale_id']
                    
                    if new_status == 'pending':
                        sale_delivery_status = 'processing'
                    elif new_status == 'in_transit':
                        sale_delivery_status = 'shipping'
                    elif new_status == 'delivered':
                        sale_delivery_status = 'delivered'
                        # Set delivery date if not already set
                        actual_delivery = data.get('actual_delivery')
                        cursor.execute("""
                            UPDATE sales 
                            SET delivery_status = %s, delivery_date = %s
                            WHERE id = %s
                        """, (sale_delivery_status, actual_delivery, sale_id))
                    else:
                        sale_delivery_status = 'processing'
                    
                    # Update sale delivery status (except for delivered which is handled above)
                    if new_status != 'delivered':
                        cursor.execute("""
                            UPDATE sales 
                            SET delivery_status = %s
                            WHERE id = %s
                        """, (sale_delivery_status, sale_id))
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Dispatch updated successfully'})
                
            except Exception as e:
                print(f"Update dispatch error: {e}")
                return jsonify({'error': f'Failed to update dispatch: {str(e)}'}), 500
        
        elif request.method == 'DELETE':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                cursor.execute("DELETE FROM dispatches WHERE id = %s", (dispatch_id,))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'Dispatch not found'}), 404
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Dispatch deleted successfully'})
                
            except Exception as e:
                print(f"Delete dispatch error: {e}")
                return jsonify({'error': f'Failed to delete dispatch: {str(e)}'}), 500
    
    @app.route('/api/v1/products/by-customer/<int:customer_id>', methods=['GET'])
    def get_customer_products(customer_id):
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT s.id as sale_id, s.sale_number,
                       GROUP_CONCAT(DISTINCT p.name ORDER BY p.name SEPARATOR ', ') as product_names,
                       SUM(si.quantity) as total_quantity
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                JOIN products p ON si.product_id = p.id
                LEFT JOIN dispatches d ON d.sale_id = s.id AND d.status != 'cancelled'
                WHERE s.customer_id = %s AND d.id IS NULL
                GROUP BY s.id, s.sale_number
                ORDER BY s.sale_date DESC
            """, (customer_id,))
            sales = cursor.fetchall()
            conn.close()
            
            return jsonify(sales)
            
        except Exception as e:
            print(f"Get customer products error: {e}")
            return jsonify([])

def register_reports_routes(app):
    @app.route('/api/v1/reports/dashboard', methods=['GET'])
    def reports_dashboard_stats():
        try:
            conn = get_db()
            if not conn:
                return jsonify({})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get totals
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            customers_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count, COALESCE(SUM(final_amount), 0) as revenue FROM sales")
            sales_data = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) as count FROM dispatches")
            dispatches_count = cursor.fetchone()['count']
            
            # Get dispatch status breakdown
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM dispatches 
                GROUP BY status
            """)
            dispatch_status = cursor.fetchall()
            
            # Get sales delivery status breakdown
            cursor.execute("""
                SELECT delivery_status, COUNT(*) as count 
                FROM sales 
                GROUP BY delivery_status
            """)
            sales_delivery = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'totals': {
                    'customers': customers_count,
                    'sales': sales_data['count'],
                    'dispatches': dispatches_count,
                    'revenue': float(sales_data['revenue'])
                },
                'dispatch_status': dispatch_status,
                'sales_delivery': sales_delivery
            })
            
        except Exception as e:
            print(f"Dashboard stats error: {e}")
            return jsonify({})
    
    @app.route('/api/v1/reports/sales', methods=['GET'])
    def reports_sales_report():
        try:
            conn = get_db()
            if not conn:
                return jsonify({'summary': {}, 'sales': []})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Build WHERE clause based on filters
            where_clauses = []
            params = []
            
            if request.args.get('start_date'):
                where_clauses.append("s.sale_date >= %s")
                params.append(request.args.get('start_date'))
            
            if request.args.get('end_date'):
                where_clauses.append("s.sale_date <= %s")
                params.append(request.args.get('end_date'))
            
            if request.args.get('customer_id'):
                where_clauses.append("s.customer_id = %s")
                params.append(int(request.args.get('customer_id')))
            
            if request.args.get('customer_type'):
                where_clauses.append("c.customer_type = %s")
                params.append(request.args.get('customer_type'))
            
            if request.args.get('sales_executive_id'):
                where_clauses.append("s.created_by = %s")
                params.append(int(request.args.get('sales_executive_id')))
            
            if request.args.get('product_id'):
                where_clauses.append("EXISTS (SELECT 1 FROM sale_items si WHERE si.sale_id = s.id AND si.product_id = %s)")
                params.append(int(request.args.get('product_id')))
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get summary
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_sales,
                    COALESCE(SUM(s.final_amount), 0) as total_revenue,
                    COALESCE(AVG(s.final_amount), 0) as avg_sale_amount
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE {where_sql}
            """, params)
            summary = cursor.fetchone()
            
            # Get sales details
            cursor.execute(f"""
                SELECT s.*, c.company_name, c.contact_person,
                       (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id) as item_count
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE {where_sql}
                ORDER BY s.sale_date DESC
            """, params)
            sales = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'summary': {
                    'total_sales': summary['total_sales'],
                    'total_revenue': float(summary['total_revenue']),
                    'avg_sale_amount': float(summary['avg_sale_amount'])
                },
                'sales': sales
            })
            
        except Exception as e:
            print(f"Sales report error: {e}")
            return jsonify({'summary': {}, 'sales': []})
    
    @app.route('/api/v1/reports/dispatch', methods=['GET'])
    def reports_dispatch_report():
        try:
            conn = get_db()
            if not conn:
                return jsonify({'summary': {}, 'dispatches': []})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Build WHERE clause
            where_clauses = []
            params = []
            
            if request.args.get('start_date'):
                where_clauses.append("d.dispatch_date >= %s")
                params.append(request.args.get('start_date'))
            
            if request.args.get('end_date'):
                where_clauses.append("d.dispatch_date <= %s")
                params.append(request.args.get('end_date'))
            
            if request.args.get('status'):
                where_clauses.append("d.status = %s")
                params.append(request.args.get('status'))
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get summary
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_dispatches,
                    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_count,
                    SUM(CASE WHEN status = 'in_transit' THEN 1 ELSE 0 END) as in_transit_count,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count
                FROM dispatches d
                WHERE {where_sql}
            """, params)
            summary = cursor.fetchone()
            
            # Get dispatch details
            cursor.execute(f"""
                SELECT d.*, c.company_name, c.contact_person,
                       GROUP_CONCAT(DISTINCT p.name SEPARATOR ', ') as product_name
                FROM dispatches d
                LEFT JOIN customers c ON d.customer_id = c.id
                LEFT JOIN sale_items si ON d.sale_id = si.sale_id
                LEFT JOIN products p ON si.product_id = p.id
                WHERE {where_sql}
                GROUP BY d.id
                ORDER BY d.dispatch_date DESC
            """, params)
            dispatches = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'summary': summary,
                'dispatches': dispatches
            })
            
        except Exception as e:
            print(f"Dispatch report error: {e}")
            return jsonify({'summary': {}, 'dispatches': []})

def register_notifications_routes(app):
    @app.route('/api/v1/notifications/', methods=['GET'])
    def get_notifications():
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            # First check if table exists
            cursor.execute("SHOW TABLES LIKE 'notifications'")
            if not cursor.fetchone():
                conn.close()
                return jsonify([])
            
            cursor.execute("""
                SELECT n.*, 
                       COALESCE(c.contact_person, c.company_name, c.individual_name) as recipient_name
                FROM notifications n
                LEFT JOIN customers c ON n.customer_id = c.id
                WHERE n.user_id IS NOT NULL
                ORDER BY n.created_at DESC
            """)
            notifications = cursor.fetchall()
            conn.close()
            return jsonify(notifications)
        except Exception as e:
            print(f"Get notifications error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/notifications/sent', methods=['GET'])
    def get_sent_notifications():
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT n.*, c.contact_person as recipient_name
                FROM notifications n
                LEFT JOIN customers c ON n.customer_id = c.id
                WHERE n.is_sent = 1
                ORDER BY n.created_at DESC
            """)
            notifications = cursor.fetchall()
            conn.close()
            return jsonify(notifications)
        except Exception as e:
            print(f"Get sent notifications error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/notifications/customers', methods=['GET'])
    def get_notification_customers():
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, 
                       COALESCE(company_name, individual_name, contact_person) as name,
                       email, phone
                FROM customers
                ORDER BY name
            """)
            customers = cursor.fetchall()
            conn.close()
            return jsonify(customers)
        except Exception as e:
            print(f"Get notification customers error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/notifications/unread-count', methods=['GET'])
    def get_unread_count():
        try:
            conn = get_db()
            if not conn:
                return jsonify({'unread_count': 0})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE is_read = 0")
            result = cursor.fetchone()
            conn.close()
            return jsonify({'unread_count': result['count']})
        except Exception as e:
            print(f"Get unread count error: {e}")
            return jsonify({'unread_count': 0})
    
    @app.route('/api/v1/notifications/<int:notification_id>/read', methods=['PUT'])
    def mark_as_read(notification_id):
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = %s", (notification_id,))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Marked as read'})
        except Exception as e:
            print(f"Mark as read error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/notifications/mark-all-read', methods=['PUT'])
    def mark_all_as_read():
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("UPDATE notifications SET is_read = 1")
            conn.commit()
            conn.close()
            return jsonify({'message': 'All marked as read'})
        except Exception as e:
            print(f"Mark all as read error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/notifications/<int:notification_id>', methods=['DELETE'])
    def delete_notification(notification_id):
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Notification deleted'})
        except Exception as e:
            print(f"Delete notification error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/notifications/send/<int:customer_id>', methods=['POST'])
    def send_to_customer(customer_id):
        try:
            data = request.get_json()
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                INSERT INTO notifications (title, message, type, customer_id, is_read, is_sent)
                VALUES (%s, %s, %s, %s, 0, 1)
            """, (data.get('title'), data.get('message'), data.get('notification_type', 'INFO').upper(), customer_id))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Notification sent'})
        except Exception as e:
            print(f"Send notification error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/notifications/broadcast', methods=['POST'])
    def broadcast_notification():
        try:
            data = request.get_json()
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT id FROM customers")
            customers = cursor.fetchall()
            
            for customer in customers:
                cursor.execute("""
                    INSERT INTO notifications (title, message, type, customer_id, is_read, is_sent)
                    VALUES (%s, %s, %s, %s, 0, 1)
                """, (data.get('title'), data.get('message'), data.get('notification_type', 'INFO').upper(), customer['id']))
            
            conn.commit()
            conn.close()
            return jsonify({'message': 'Broadcast sent'})
        except Exception as e:
            print(f"Broadcast notification error: {e}")
            return jsonify({'error': str(e)}), 500

def register_specifications_routes(app):
    @app.route('/api/v1/specifications/', methods=['GET'])
    @jwt_required()
    def get_specifications():
        """Get system specifications and documentation"""
        return jsonify({
            'system': {
                'name': 'Product Images Management System',
                'version': '1.0.0',
                'description': 'Comprehensive product image management with cloud storage'
            },
            'architecture': {
                'frontend': 'React + TypeScript + Bootstrap',
                'backend': 'Flask + Python + MySQL',
                'storage': 'Hostinger Cloud Storage',
                'database_tables': ['products', 'product_images']
            },
            'features': {
                'core': [
                    'Multi-file upload system',
                    'Primary image management',
                    'Cloud storage integration',
                    'Real-time synchronization',
                    'Responsive UI design'
                ],
                'enhancements': [
                    'Gradient UI elements',
                    'Animation effects',
                    'Toast notifications',
                    'Drag & drop upload',
                    'Image preview system'
                ]
            },
            'api_endpoints': {
                'image_management': [
                    'GET /api/v1/product-images/{product_id}',
                    'POST /api/v1/product-images/upload/{product_id}',
                    'PUT /api/v1/product-images/{image_id}/set-primary',
                    'DELETE /api/v1/product-images/delete/{image_id}'
                ],
                'bulk_operations': [
                    'POST /api/v1/product-images/bulk-upload',
                    'POST /api/v1/product-images/sync-existing'
                ]
            },
            'security': {
                'authentication': 'JWT Token Based',
                'file_validation': 'Type and size validation',
                'data_protection': 'SQL injection prevention, XSS protection'
            },
            'performance': {
                'frontend': 'Lazy loading, image optimization, caching',
                'backend': 'Query optimization, connection pooling, batch operations'
            }
        })
    
    @app.route('/api/v1/products/<int:product_id>/specifications', methods=['GET', 'POST', 'DELETE'])
    def handle_product_specifications(product_id):
        """Get, add, or delete product specifications"""
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute(
                    "SELECT * FROM product_specifications WHERE product_id = %s ORDER BY display_order, id",
                    (product_id,)
                )
                specs = cursor.fetchall()
                conn.close()
                
                # Map database fields to frontend expected fields
                mapped_specs = []
                for spec in specs:
                    mapped_specs.append({
                        'id': spec.get('id'),
                        'product_id': spec.get('product_id'),
                        'spec_name': spec.get('feature_name'),
                        'spec_value': spec.get('feature_value'),
                        'spec_category': spec.get('category'),
                        'display_order': spec.get('display_order'),
                        'created_at': spec.get('created_at'),
                        'updated_at': spec.get('updated_at')
                    })
                
                return jsonify(mapped_specs)
                
            except Exception as e:
                print(f"Get product specifications error: {e}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                print(f"Received data: {data}")  # Debug log
                
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                # Handle nested specifications array
                if 'specifications' in data and isinstance(data['specifications'], list) and len(data['specifications']) > 0:
                    spec_data = data['specifications'][0]  # Take first specification
                else:
                    spec_data = data  # Use data directly if not nested
                
                # Extract fields from the specification data
                feature_name = spec_data.get('spec_name') or spec_data.get('feature_name') or spec_data.get('name')
                feature_value = spec_data.get('spec_value') or spec_data.get('feature_value') or spec_data.get('value')
                category = spec_data.get('spec_category') or spec_data.get('category', 'General')
                
                print(f"Extracted - feature_name: '{feature_name}', feature_value: '{feature_value}', category: '{category}'")  # Debug log
                
                if not feature_name or feature_name.strip() == '':
                    return jsonify({'error': 'spec_name is required and cannot be empty', 'received_data': data}), 400
                if not feature_value or feature_value.strip() == '':
                    return jsonify({'error': 'spec_value is required and cannot be empty', 'received_data': data}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Insert specification using correct column names
                cursor.execute(
                    "INSERT INTO product_specifications (product_id, feature_name, feature_value, category) VALUES (%s, %s, %s, %s)",
                    (product_id, feature_name.strip(), feature_value.strip(), category.strip())
                )
                conn.commit()
                spec_id = cursor.lastrowid
                conn.close()
                
                return jsonify({
                    'id': spec_id,
                    'product_id': product_id,
                    'feature_name': feature_name.strip(),
                    'feature_value': feature_value.strip(),
                    'category': category.strip()
                }), 201
                
            except Exception as e:
                print(f"Add product specification error: {e}")
                return jsonify({'error': f'Failed to add specification: {str(e)}'}), 500
        
        elif request.method == 'DELETE':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # Delete all specifications for this product
                cursor.execute(
                    "DELETE FROM product_specifications WHERE product_id = %s",
                    (product_id,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                return jsonify({
                    'message': f'Deleted {deleted_count} specifications',
                    'deleted_count': deleted_count
                }), 200
                
            except Exception as e:
                print(f"Delete product specifications error: {e}")
                return jsonify({'error': f'Failed to delete specifications: {str(e)}'}), 500
    
    @app.route('/api/v1/products/specifications/<int:spec_id>', methods=['DELETE'])
    def delete_single_specification(spec_id):
        """Delete a single product specification by ID"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Delete specific specification
            cursor.execute(
                "DELETE FROM product_specifications WHERE id = %s",
                (spec_id,)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                return jsonify({
                    'message': f'Specification {spec_id} deleted successfully',
                    'deleted_count': deleted_count
                }), 200
            else:
                return jsonify({'error': 'Specification not found'}), 404
                
        except Exception as e:
            print(f"Delete specification error: {e}")
            return jsonify({'error': f'Failed to delete specification: {str(e)}'}), 500
