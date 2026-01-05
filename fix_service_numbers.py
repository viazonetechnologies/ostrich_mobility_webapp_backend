import pymysql

# Fix existing service tickets with timestamp format
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Find service tickets with timestamp format
cursor.execute("SELECT id, ticket_number FROM service_tickets WHERE ticket_number LIKE 'TKT%' AND LENGTH(ticket_number) > 9")
timestamp_tickets = cursor.fetchall()

print("Found service tickets with timestamp format:")
for ticket in timestamp_tickets:
    print(f"ID: {ticket[0]}, Number: {ticket[1]}")

# Update timestamp tickets to proper format
if timestamp_tickets:
    for ticket in timestamp_tickets:
        ticket_id = ticket[0]
        new_number = f"TKT{ticket_id:06d}"
        cursor.execute("UPDATE service_tickets SET ticket_number = %s WHERE id = %s", (new_number, ticket_id))
        print(f"Updated ticket ID {ticket_id} from {ticket[1]} to {new_number}")

connection.commit()

# Verify the fix
cursor.execute("SELECT id, ticket_number, customer_id, created_at FROM service_tickets ORDER BY id DESC LIMIT 5")
tickets = cursor.fetchall()

print("\nUpdated service tickets:")
for ticket in tickets:
    print(f"ID: {ticket[0]}, Number: {ticket[1]}, Customer: {ticket[2]}, Created: {ticket[3]}")

connection.close()
print("\nService ticket numbers fixed successfully!")