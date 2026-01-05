import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Aru247899!',
        database='ostrich_db',
        port=3306,
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    # Check if we have customers and products
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    print(f"Customers: {customer_count}, Products: {product_count}")
    
    if customer_count == 0:
        print("Adding sample customers...")
        cursor.execute("""
            INSERT INTO customers (customer_code, customer_type, company_name, contact_person, email, phone, address, city, state, country, pin_code)
            VALUES 
            ('CUS000001', 'b2b', 'Tech Solutions Ltd', 'John Smith', 'john@techsolutions.com', '9876543210', '123 Business St', 'Mumbai', 'Maharashtra', 'India', '400001'),
            ('CUS000002', 'b2c', 'ABC Corp', 'Jane Doe', 'jane@abccorp.com', '9876543211', '456 Corporate Ave', 'Delhi', 'Delhi', 'India', '110001'),
            ('CUS000003', 'b2b', 'XYZ Industries', 'Bob Wilson', 'bob@xyzind.com', '9876543212', '789 Industrial Rd', 'Bangalore', 'Karnataka', 'India', '560001')
        """)
        connection.commit()
        print("Sample customers added")
    
    if product_count == 0:
        print("Adding sample products...")
        cursor.execute("""
            INSERT INTO products (product_code, name, description, category_id, price, is_active)
            VALUES 
            ('PRD000001', '3HP Single Phase Motor', 'High efficiency 3HP motor for industrial use', 1, 25000.00, 1),
            ('PRD000002', '5HP Three Phase Motor', 'Heavy duty 5HP motor for commercial applications', 1, 35000.00, 1),
            ('PRD000003', '10HP Motor', 'Industrial grade 10HP motor', 1, 45000.00, 1),
            ('PRD000004', 'Electric Wheelchair', 'Premium electric wheelchair with advanced features', 2, 85000.00, 1),
            ('PRD000005', 'Hospital Bed', 'Adjustable hospital bed with remote control', 3, 65000.00, 1)
        """)
        connection.commit()
        print("Sample products added")
    
    # Check if we have sales
    cursor.execute("SELECT COUNT(*) FROM sales")
    sales_count = cursor.fetchone()[0]
    
    if sales_count == 0:
        print("Adding sample sales...")
        cursor.execute("""
            INSERT INTO sales (sale_number, customer_id, sale_date, total_amount, final_amount, payment_status, delivery_status)
            VALUES 
            ('SAL000001', 1, '2025-12-01', 25000.00, 25000.00, 'paid', 'pending'),
            ('SAL000002', 2, '2025-12-02', 35000.00, 35000.00, 'paid', 'pending'),
            ('SAL000003', 3, '2025-12-03', 45000.00, 45000.00, 'pending', 'pending'),
            ('SAL000004', 1, '2025-12-04', 85000.00, 85000.00, 'paid', 'pending'),
            ('SAL000005', 2, '2025-12-05', 65000.00, 65000.00, 'paid', 'pending')
        """)
        connection.commit()
        
        # Add sale items
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
            VALUES 
            (1, 1, 1, 25000.00, 25000.00),
            (2, 2, 1, 35000.00, 35000.00),
            (3, 3, 1, 45000.00, 45000.00),
            (4, 4, 1, 85000.00, 85000.00),
            (5, 5, 1, 65000.00, 65000.00)
        """)
        connection.commit()
        print("Sample sales and sale items added")
    
    # Now check what products each customer has purchased
    cursor.execute("""
        SELECT c.id, c.contact_person, p.id, p.name
        FROM customers c
        JOIN sales s ON c.id = s.customer_id
        JOIN sale_items si ON s.id = si.sale_id
        JOIN products p ON si.product_id = p.id
        ORDER BY c.id, p.name
    """)
    
    results = cursor.fetchall()
    print("\nCustomer purchases:")
    for row in results:
        print(f"Customer {row[0]} ({row[1]}) purchased Product {row[2]} ({row[3]})")
    
    connection.close()
    print("\nSample data setup complete!")
    
except Exception as e:
    print(f"Error: {e}")