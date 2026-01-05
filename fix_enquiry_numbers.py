#!/usr/bin/env python3
import pymysql

def fix_enquiry_numbers():
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
        
        # First, let's see what we have
        print("=== BEFORE FIXING ===")
        cursor.execute("SELECT id, enquiry_number, customer_id, created_at FROM enquiries ORDER BY id")
        enquiries = cursor.fetchall()
        
        print(f"Total enquiries: {len(enquiries)}")
        for enq in enquiries:
            print(f"ID: {enq[0]}, Number: {enq[1]}, Customer: {enq[2]}, Created: {enq[3]}")
        
        # Update all enquiry numbers to sequential format based on ID
        print("\n=== FIXING ENQUIRY NUMBERS ===")
        cursor.execute("""
            UPDATE enquiries 
            SET enquiry_number = CONCAT('ENQ', LPAD(id, 6, '0'))
            WHERE enquiry_number IS NULL 
               OR enquiry_number NOT LIKE 'ENQ______'
               OR LENGTH(enquiry_number) != 9
               OR enquiry_number REGEXP '^ENQ[0-9]{10,}$'
        """)
        
        rows_affected = cursor.rowcount
        print(f"Updated {rows_affected} enquiry numbers")
        
        connection.commit()
        
        # Verify the changes
        print("\n=== AFTER FIXING ===")
        cursor.execute("SELECT id, enquiry_number, customer_id, created_at FROM enquiries ORDER BY id")
        enquiries = cursor.fetchall()
        
        for enq in enquiries:
            print(f"ID: {enq[0]}, Number: {enq[1]}, Customer: {enq[2]}, Created: {enq[3]}")
        
        # Show statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_enquiries,
                COUNT(CASE WHEN enquiry_number LIKE 'ENQ______' THEN 1 END) as proper_format,
                COUNT(CASE WHEN enquiry_number NOT LIKE 'ENQ______' THEN 1 END) as needs_fixing
            FROM enquiries
        """)
        
        stats = cursor.fetchone()
        print(f"\n=== STATISTICS ===")
        print(f"Total enquiries: {stats[0]}")
        print(f"Proper format (ENQ######): {stats[1]}")
        print(f"Still needs fixing: {stats[2]}")
        
        connection.close()
        print("\n✅ Enquiry numbers fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing enquiry numbers: {e}")

if __name__ == "__main__":
    fix_enquiry_numbers()