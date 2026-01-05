#!/usr/bin/env python3
import pymysql

def show_customer_names():
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
        
        print("=== CUSTOMERS TABLE ===")
        cursor.execute("SELECT id, contact_person, company_name, email FROM customers ORDER BY id")
        customers = cursor.fetchall()
        
        for customer in customers:
            print(f"ID: {customer[0]} | Contact: {customer[1]} | Company: {customer[2]} | Email: {customer[3]}")
        
        print(f"\nTotal customers: {len(customers)}")
        
        print("\n=== SERVICE TICKETS WITH CUSTOMER MAPPING ===")
        cursor.execute("""
            SELECT st.id, st.ticket_number, st.customer_id, 
                   c.contact_person, c.company_name
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            ORDER BY st.id DESC
            LIMIT 10
        """)
        
        tickets = cursor.fetchall()
        for ticket in tickets:
            customer_display = ticket[3] or ticket[4] or f"Unknown (ID: {ticket[2]})"
            print(f"Ticket {ticket[1]} -> Customer ID: {ticket[2]} -> Name: {customer_display}")
        
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_customer_names()