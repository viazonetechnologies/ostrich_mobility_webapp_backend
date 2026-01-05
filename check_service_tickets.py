import pymysql

# Check current service tickets
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Check service tickets
cursor.execute("SELECT id, ticket_number, customer_id, issue_description, priority, status, created_at FROM service_tickets ORDER BY id DESC LIMIT 10")
tickets = cursor.fetchall()

print("Current service tickets:")
for ticket in tickets:
    print(f"ID: {ticket[0]}, Number: {ticket[1]}, Customer: {ticket[2]}, Issue: {ticket[3][:20]}..., Priority: {ticket[4]}, Status: {ticket[5]}, Created: {ticket[6]}")

connection.close()