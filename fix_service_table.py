#!/usr/bin/env python3
import pymysql

def fix_service_table():
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
        
        # Check current table structure
        cursor.execute("DESCRIBE service_tickets")
        columns = cursor.fetchall()
        print("Current table structure:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
        # Fix status column length
        cursor.execute("ALTER TABLE service_tickets MODIFY status VARCHAR(20)")
        print("Extended status column length")
        
        # Fix priority column length  
        cursor.execute("ALTER TABLE service_tickets MODIFY priority VARCHAR(20)")
        print("Extended priority column length")
        
        # Now fix the data
        cursor.execute("UPDATE service_tickets SET priority = 'MEDIUM' WHERE priority NOT IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')")
        priority_fixed = cursor.rowcount
        print(f"Fixed {priority_fixed} priority values")
        
        cursor.execute("UPDATE service_tickets SET status = 'OPEN' WHERE status NOT IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')")
        status_fixed = cursor.rowcount
        print(f"Fixed {status_fixed} status values")
        
        connection.commit()
        connection.close()
        print("Service tickets table and data fixed!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_service_table()