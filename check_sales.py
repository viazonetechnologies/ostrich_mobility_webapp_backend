#!/usr/bin/env python3
import pymysql

def check_sales_data():
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
        
        # Check sales table structure
        print("=== SALES TABLE STRUCTURE ===")
        cursor.execute("DESCRIBE sales")
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[0]}: {col[1]}")
        
        # Check sales data
        print("\n=== SALES DATA ===")
        cursor.execute("""
            SELECT s.id, s.sale_number, s.customer_id, s.sale_date, s.total_amount, 
                   s.payment_status, s.delivery_status, s.created_at,
                   c.contact_person as customer_name
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            ORDER BY s.id DESC
            LIMIT 10
        """)
        
        sales = cursor.fetchall()
        print(f"Total sales found: {len(sales)}")
        
        for sale in sales:
            print(f"\nSale ID: {sale[0]}")
            print(f"  Number: {sale[1]}")
            print(f"  Customer: {sale[8]} (ID: {sale[2]})")
            print(f"  Date: {sale[3]}")
            print(f"  Amount: {sale[4]}")
            print(f"  Payment: {sale[5]}")
            print(f"  Delivery: {sale[6]}")
        
        # Check sale_items
        print("\n=== SALE_ITEMS TABLE ===")
        cursor.execute("DESCRIBE sale_items")
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[0]}: {col[1]}")
        
        cursor.execute("""
            SELECT si.id, si.sale_id, si.product_id, si.quantity, si.unit_price,
                   p.name as product_name
            FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.id
            ORDER BY si.id DESC
            LIMIT 10
        """)
        
        items = cursor.fetchall()
        print(f"\nSale items found: {len(items)}")
        
        for item in items:
            print(f"Item ID: {item[0]} | Sale: {item[1]} | Product: {item[5]} | Qty: {item[3]} | Price: {item[4]}")
        
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_sales_data()