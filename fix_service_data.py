import pymysql

# Fix service tickets data issues
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Fix any remaining timestamp tickets
cursor.execute("SELECT id, ticket_number FROM service_tickets WHERE ticket_number LIKE 'TKT%' AND LENGTH(ticket_number) > 9")
timestamp_tickets = cursor.fetchall()

for ticket in timestamp_tickets:
    ticket_id = ticket[0]
    new_number = f"TKT{ticket_id:06d}"
    cursor.execute("UPDATE service_tickets SET ticket_number = %s WHERE id = %s", (new_number, ticket_id))
    print(f"Fixed ticket ID {ticket_id} from {ticket[1]} to {new_number}")

connection.commit()

# Check service tickets data with proper joins
cursor.execute("""
    SELECT st.id, st.ticket_number, st.customer_id, st.product_id, st.issue_description, 
           st.priority, st.status, st.assigned_staff_id, st.scheduled_date,
           c.contact_person, c.company_name,
           p.name as product_name,
           CONCAT(u.first_name, ' ', u.last_name) as staff_name
    FROM service_tickets st
    LEFT JOIN customers c ON st.customer_id = c.id
    LEFT JOIN products p ON st.product_id = p.id
    LEFT JOIN users u ON st.assigned_staff_id = u.id
    ORDER BY st.id DESC LIMIT 5
""")

tickets = cursor.fetchall()
print("\nService tickets with proper data:")
for ticket in tickets:
    print(f"ID: {ticket[0]}")
    print(f"  Ticket: {ticket[1]}")
    print(f"  Customer: {ticket[9] or ticket[10] or 'Unknown'}")
    print(f"  Product: {ticket[11] or 'Unknown'}")
    print(f"  Issue: {ticket[4]}")
    print(f"  Priority: {ticket[5]}")
    print(f"  Status: {ticket[6]}")
    print(f"  Staff: {ticket[12] or 'Unassigned'}")
    print(f"  Scheduled: {ticket[8]}")
    print("---")

connection.close()