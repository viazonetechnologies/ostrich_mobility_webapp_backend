#!/usr/bin/env python3
import pymysql

def show_service_tickets_data():
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
        
        # Show table structure
        print("=== SERVICE_TICKETS TABLE STRUCTURE ===")
        cursor.execute("DESCRIBE service_tickets")
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[0]}: {col[1]} ({col[2]}, {col[3]}, {col[4]})")
        
        # Show actual data
        print("\n=== ACTUAL DATA (First 5 records) ===")
        cursor.execute("""
            SELECT id, ticket_number, customer_id, product_id, issue_description, 
                   priority, status, assigned_staff_id, scheduled_date, created_at
            FROM service_tickets 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        tickets = cursor.fetchall()
        for ticket in tickets:
            print(f"\nID: {ticket[0]}")
            print(f"  Ticket Number: {ticket[1]}")
            print(f"  Customer ID: {ticket[2]}")
            print(f"  Product ID: {ticket[3]}")
            print(f"  Issue: {ticket[4]}")
            print(f"  Priority: {ticket[5]}")
            print(f"  Status: {ticket[6]}")
            print(f"  Staff ID: {ticket[7]}")
            print(f"  Scheduled: {ticket[8]}")
            print(f"  Created: {ticket[9]}")
        
        # Show joined data
        print("\n=== JOINED DATA WITH NAMES ===")
        cursor.execute("""
            SELECT st.id, st.ticket_number, 
                   c.contact_person as customer_name,
                   p.name as product_name,
                   st.issue_description,
                   st.priority, st.status,
                   CONCAT(u.first_name, ' ', u.last_name) as staff_name
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            LEFT JOIN products p ON st.product_id = p.id
            LEFT JOIN users u ON st.assigned_staff_id = u.id
            ORDER BY st.id DESC 
            LIMIT 5
        """)
        
        tickets = cursor.fetchall()
        for ticket in tickets:
            print(f"\nID: {ticket[0]} | Ticket: {ticket[1]}")
            print(f"  Customer: {ticket[2]}")
            print(f"  Product: {ticket[3]}")
            print(f"  Issue: {ticket[4]}")
            print(f"  Priority: {ticket[5]} | Status: {ticket[6]}")
            print(f"  Staff: {ticket[7]}")
        
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_service_tickets_data()