import pymysql

# Fix the latest service ticket with timestamp format
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Find and fix any remaining timestamp tickets
cursor.execute("SELECT id, ticket_number FROM service_tickets WHERE ticket_number LIKE 'TKT%' AND LENGTH(ticket_number) > 9")
timestamp_tickets = cursor.fetchall()

print("Found service tickets with timestamp format:")
for ticket in timestamp_tickets:
    print(f"ID: {ticket[0]}, Number: {ticket[1]}")
    new_number = f"TKT{ticket[0]:06d}"
    cursor.execute("UPDATE service_tickets SET ticket_number = %s WHERE id = %s", (new_number, ticket[0]))
    print(f"Updated to: {new_number}")

connection.commit()

# Show current tickets
cursor.execute("SELECT id, ticket_number, customer_id FROM service_tickets ORDER BY id DESC LIMIT 5")
tickets = cursor.fetchall()

print("\nCurrent service tickets:")
for ticket in tickets:
    print(f"ID: {ticket[0]}, Number: {ticket[1]}, Customer: {ticket[2]}")

connection.close()
print("\nAll service ticket numbers fixed!")