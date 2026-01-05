#!/usr/bin/env python3
import pymysql
import json

def simulate_sales_response():
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
        
        # Execute the Flask sales query
        cursor.execute("""
            SELECT s.id, s.sale_number, s.customer_id, s.sale_date, s.total_amount, 
                   s.discount_percentage, s.discount_amount, s.final_amount, 
                   s.payment_status, s.delivery_status, s.delivery_date, 
                   s.delivery_address, s.notes, s.created_by, s.created_at,
                   COALESCE(c.contact_person, c.company_name, 'Unknown Customer') as customer_name,
                   GROUP_CONCAT(CONCAT(p.name, ' (', si.quantity, ')') SEPARATOR ', ') as items
            FROM sales s 
            LEFT JOIN customers c ON s.customer_id = c.id
            LEFT JOIN sale_items si ON s.id = si.sale_id
            LEFT JOIN products p ON si.product_id = p.id
            GROUP BY s.id
            ORDER BY s.id DESC
            LIMIT 10
        """)
        
        sales_db = cursor.fetchall()
        
        print("=== FLASK SALES API RESPONSE ===")
        result = []
        
        for sale in sales_db:
            sale_data = {
                "id": sale[0],
                "sale_number": sale[1],
                "customer_id": sale[2],
                "customer_name": sale[15],
                "sale_date": str(sale[3]) if sale[3] else None,
                "total_amount": float(sale[4]) if sale[4] else 0.0,
                "discount_percentage": float(sale[5]) if sale[5] else 0.0,
                "discount_amount": float(sale[6]) if sale[6] else 0.0,
                "final_amount": float(sale[7]) if sale[7] else 0.0,
                "payment_status": sale[8] if sale[8] else "pending",
                "delivery_status": sale[9] if sale[9] else "pending",
                "delivery_date": str(sale[10]) if sale[10] else None,
                "delivery_address": sale[11],
                "notes": sale[12],
                "created_by": sale[13],
                "created_at": str(sale[14]) if sale[14] else None,
                "items": sale[16] if sale[16] else "No items"
            }
            result.append(sale_data)
            
            print(f"\nSale {sale_data['sale_number']}:")
            print(f"  Customer: {sale_data['customer_name']}")
            print(f"  Date: {sale_data['sale_date']}")
            print(f"  Amount: ${sale_data['final_amount']}")
            print(f"  Payment: {sale_data['payment_status']}")
            print(f"  Delivery: {sale_data['delivery_status']}")
            print(f"  Items: {sale_data['items']}")
        
        # Save to file
        with open('sales_response.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n✅ Sales response saved to sales_response.json")
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simulate_sales_response()