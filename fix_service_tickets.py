#!/usr/bin/env python3
import pymysql

def fix_service_tickets():
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
        
        # Check current service tickets
        print("=== CHECKING SERVICE TICKETS ===")
        cursor.execute("""
            SELECT id, ticket_number, customer_id, product_id, issue_description, 
                   priority, status, assigned_staff_id, created_at
            FROM service_tickets 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        tickets = cursor.fetchall()
        print(f"Recent service tickets:")
        for ticket in tickets:
            print(f"ID: {ticket[0]}, Number: {ticket[1]}, Customer: {ticket[2]}, Product: {ticket[3]}")
            print(f"  Issue: {ticket[4]}, Priority: {ticket[5]}, Status: {ticket[6]}")
        
        # Fix invalid priority values
        print(\"\\n=== FIXING PRIORITY VALUES ===\")
        cursor.execute(\"\"\"
            UPDATE service_tickets 
            SET priority = CASE 
                WHEN priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT') THEN priority
                WHEN priority LIKE '%HIGH%' OR priority LIKE '%URGENT%' THEN 'HIGH'
                WHEN priority LIKE '%LOW%' THEN 'LOW'
                ELSE 'MEDIUM'
            END
            WHERE priority NOT IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')
        \"\"\")\n        
        priority_fixed = cursor.rowcount
        print(f\"Fixed {priority_fixed} priority values\")
        
        # Fix invalid status values
        print(\"\\n=== FIXING STATUS VALUES ===\")
        cursor.execute(\"\"\"
            UPDATE service_tickets 
            SET status = CASE 
                WHEN status IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') THEN status
                WHEN status LIKE '%PROGRESS%' OR status LIKE '%WORKING%' THEN 'IN_PROGRESS'
                WHEN status LIKE '%COMPLETE%' OR status LIKE '%DONE%' THEN 'COMPLETED'
                WHEN status LIKE '%CANCEL%' THEN 'CANCELLED'
                ELSE 'OPEN'
            END
            WHERE status NOT IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')
        \"\"\")\n        
        status_fixed = cursor.rowcount
        print(f\"Fixed {status_fixed} status values\")
        
        # Ensure all tickets have valid customer_id and product_id
        print(\"\\n=== FIXING CUSTOMER AND PRODUCT REFERENCES ===\")
        
        # Get first available customer and product
        cursor.execute(\"SELECT id FROM customers WHERE id IS NOT NULL ORDER BY id LIMIT 1\")
        default_customer = cursor.fetchone()
        default_customer_id = default_customer[0] if default_customer else 1
        
        cursor.execute(\"SELECT id FROM products WHERE is_active = 1 ORDER BY id LIMIT 1\")
        default_product = cursor.fetchone()
        default_product_id = default_product[0] if default_product else 1
        
        # Fix null customer_id
        cursor.execute(\"\"\"
            UPDATE service_tickets 
            SET customer_id = %s 
            WHERE customer_id IS NULL 
               OR customer_id NOT IN (SELECT id FROM customers)
        \"\"\", (default_customer_id,))
        
        customer_fixed = cursor.rowcount
        print(f\"Fixed {customer_fixed} customer references\")
        
        # Fix null product_id
        cursor.execute(\"\"\"
            UPDATE service_tickets 
            SET product_id = %s 
            WHERE product_id IS NULL 
               OR product_id NOT IN (SELECT id FROM products WHERE is_active = 1)
        \"\"\", (default_product_id,))
        
        product_fixed = cursor.rowcount
        print(f\"Fixed {product_fixed} product references\")
        
        # Fix null issue descriptions
        cursor.execute(\"\"\"
            UPDATE service_tickets 
            SET issue_description = 'Service required - no description provided'
            WHERE issue_description IS NULL OR issue_description = ''
        \"\"\")
        
        description_fixed = cursor.rowcount
        print(f\"Fixed {description_fixed} issue descriptions\")
        
        connection.commit()
        
        # Verify the fixes
        print(\"\\n=== AFTER FIXING ===\")
        cursor.execute(\"\"\"
            SELECT st.id, st.ticket_number, st.priority, st.status,
                   c.contact_person as customer_name, p.name as product_name,
                   st.issue_description
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            LEFT JOIN products p ON st.product_id = p.id
            ORDER BY st.id DESC 
            LIMIT 10
        \"\"\")
        
        tickets = cursor.fetchall()
        for ticket in tickets:
            print(f\"ID: {ticket[0]}, Number: {ticket[1]}, Priority: {ticket[2]}, Status: {ticket[3]}\")
            print(f\"  Customer: {ticket[4]}, Product: {ticket[5]}\")
            print(f\"  Issue: {ticket[6][:50]}...\")
        
        connection.close()
        print(\"\\nService tickets data fixed successfully!\")
        
    except Exception as e:
        print(f\"Error fixing service tickets: {e}\")

if __name__ == \"__main__\":
    fix_service_tickets()