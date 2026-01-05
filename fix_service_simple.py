#!/usr/bin/env python3
import pymysql

def fix_service_tickets():
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
        
        # Fix priority values
        cursor.execute("""
            UPDATE service_tickets 
            SET priority = 'MEDIUM'
            WHERE priority NOT IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')
        """)
        priority_fixed = cursor.rowcount
        print(f"Fixed {priority_fixed} priority values")
        
        # Fix status values  
        cursor.execute("""
            UPDATE service_tickets 
            SET status = 'OPEN'
            WHERE status NOT IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')
        """)
        status_fixed = cursor.rowcount
        print(f"Fixed {status_fixed} status values")
        
        # Fix issue descriptions
        cursor.execute("""
            UPDATE service_tickets 
            SET issue_description = 'Service required'
            WHERE issue_description IS NULL OR LENGTH(issue_description) < 5
        """)
        desc_fixed = cursor.rowcount
        print(f"Fixed {desc_fixed} issue descriptions")
        
        connection.commit()
        connection.close()
        print("Service tickets fixed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_service_tickets()