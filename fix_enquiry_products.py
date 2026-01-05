#!/usr/bin/env python3
import pymysql

def fix_enquiry_products():
    try:
        # Connect to database
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Aru247899!',
            database='ostrich_db',
            port=3306,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Check current enquiry-product relationships
        print("=== CHECKING ENQUIRY-PRODUCT RELATIONSHIPS ===")
        cursor.execute("""
            SELECT e.id, e.enquiry_number, e.product_id, p.name as product_name
            FROM enquiries e
            LEFT JOIN products p ON e.product_id = p.id
            ORDER BY e.id DESC
            LIMIT 10
        """)
        
        enquiries = cursor.fetchall()
        print(f"Recent enquiries:")
        for enq in enquiries:
            print(f"ID: {enq[0]}, Number: {enq[1]}, Product ID: {enq[2]}, Product Name: {enq[3]}")
        
        # Check available products
        print("\n=== AVAILABLE PRODUCTS ===")
        cursor.execute("SELECT id, name FROM products WHERE is_active = 1 ORDER BY id LIMIT 10")
        products = cursor.fetchall()
        for prod in products:
            print(f"Product ID: {prod[0]}, Name: {prod[1]}")
        
        # Update enquiries that have NULL or invalid product_id
        print("\n=== FIXING PRODUCT REFERENCES ===")
        
        # Set a default product for enquiries without valid product_id
        if products:
            default_product_id = products[0][0]  # Use first available product
            
            cursor.execute("""
                UPDATE enquiries 
                SET product_id = %s 
                WHERE product_id IS NULL 
                   OR product_id NOT IN (SELECT id FROM products WHERE is_active = 1)
            """, (default_product_id,))
            
            rows_affected = cursor.rowcount
            print(f"Updated {rows_affected} enquiries with default product ID: {default_product_id}")
            
            connection.commit()
        
        # Verify the fix
        print("\n=== AFTER FIXING ===")
        cursor.execute("""
            SELECT e.id, e.enquiry_number, e.product_id, p.name as product_name
            FROM enquiries e
            LEFT JOIN products p ON e.product_id = p.id
            ORDER BY e.id DESC
            LIMIT 10
        """)
        
        enquiries = cursor.fetchall()
        for enq in enquiries:
            print(f"ID: {enq[0]}, Number: {enq[1]}, Product ID: {enq[2]}, Product Name: {enq[3]}")
        
        connection.close()
        print("\nEnquiry-product relationships fixed!")
        
    except Exception as e:
        print(f"Error fixing enquiry products: {e}")

if __name__ == "__main__":
    fix_enquiry_products()