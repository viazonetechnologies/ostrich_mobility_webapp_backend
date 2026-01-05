#!/usr/bin/env python3
import pymysql
import json

def simulate_flask_response():
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
        
        # Execute the exact query from Flask services endpoint
        cursor.execute("""
            SELECT st.id, st.ticket_number, st.customer_id, st.product_id, 
                   st.issue_description, st.priority, st.status, st.assigned_staff_id,
                   st.scheduled_date, st.completed_date, st.service_notes, 
                   st.customer_feedback, st.rating, st.created_at,
                   COALESCE(c.contact_person, c.company_name, 'Unknown Customer') as customer_name,
                   COALESCE(p.name, 'Unknown Product') as product_name,
                   COALESCE(CONCAT(u.first_name, ' ', u.last_name), 'Service Engineer') as staff_name
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            LEFT JOIN products p ON st.product_id = p.id
            LEFT JOIN users u ON st.assigned_staff_id = u.id
            ORDER BY st.id DESC
            LIMIT 5
        """)
        
        services_db = cursor.fetchall()
        
        print("=== FLASK API RESPONSE SIMULATION ===")
        result = []
        for service in services_db:
            ticket_data = {
                "id": service[0],
                "ticket_number": service[1] if service[1] else f"TKT{service[0]:06d}",
                "customer_id": service[2],
                "customer_name": service[14],
                "product_id": service[3],
                "product_name": service[15],
                "issue_description": service[4] if service[4] else "No description provided",
                "priority": service[5] if service[5] in ['LOW', 'MEDIUM', 'HIGH', 'URGENT'] else "MEDIUM",
                "status": service[6] if service[6] in ['OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'] else "OPEN",
                "assigned_staff_id": service[7],
                "assigned_staff_name": service[16],
                "scheduled_date": str(service[8]) if service[8] else None,
                "completed_date": str(service[9]) if service[9] else None,
                "service_notes": service[10] if service[10] else "",
                "customer_feedback": service[11],
                "rating": service[12],
                "created_at": str(service[13]) if service[13] else None
            }
            result.append(ticket_data)
            
            print(f"\nTicket {ticket_data['ticket_number']}:")
            print(f"  Customer: {ticket_data['customer_name']}")
            print(f"  Product: {ticket_data['product_name']}")
            print(f"  Staff: {ticket_data['assigned_staff_name']}")
            print(f"  Issue: {ticket_data['issue_description']}")
            print(f"  Priority: {ticket_data['priority']}")
            print(f"  Status: {ticket_data['status']}")
            print(f"  Created: {ticket_data['created_at']}")
        
        # Save to file for inspection
        with open('flask_response.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n✅ Simulated response saved to flask_response.json")
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simulate_flask_response()