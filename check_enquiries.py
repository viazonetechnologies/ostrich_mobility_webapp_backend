import pymysql

# Check current enquiries in database
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Get all enquiries
cursor.execute("SELECT id, enquiry_number, customer_id, created_at FROM enquiries ORDER BY id DESC LIMIT 10")
enquiries = cursor.fetchall()

print("Current enquiries in database:")
for enq in enquiries:
    print(f"ID: {enq[0]}, Number: {enq[1]}, Customer: {enq[2]}, Created: {enq[3]}")

# Get max ID
cursor.execute("SELECT MAX(id) FROM enquiries")
max_id = cursor.fetchone()[0] or 0
print(f"\nMax enquiry ID: {max_id}")
print(f"Next enquiry number should be: ENQ{(max_id + 1):06d}")

connection.close()