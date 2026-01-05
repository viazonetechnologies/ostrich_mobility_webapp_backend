import pymysql

# Direct database test to insert enquiry with correct format
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Get max ID
cursor.execute("SELECT MAX(id) FROM enquiries")
max_id = cursor.fetchone()[0] or 0
enquiry_number = f"ENQ{(max_id + 1):06d}"

print(f"Max ID: {max_id}")
print(f"Next enquiry number: {enquiry_number}")

# Insert directly
cursor.execute("""
    INSERT INTO enquiries (enquiry_number, customer_id, product_id, quantity, 
                         message, status, assigned_to, follow_up_date, notes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    enquiry_number,
    1,  # customer_id
    1,  # product_id
    1,  # quantity
    "Direct database insert test",
    "new",
    None,
    None,
    "Testing direct insert"
))

connection.commit()
new_id = cursor.lastrowid

print(f"Inserted enquiry with ID: {new_id}")

# Verify
cursor.execute("SELECT id, enquiry_number, message FROM enquiries WHERE id = %s", (new_id,))
result = cursor.fetchone()
print(f"Verification: ID={result[0]}, Number={result[1]}, Message={result[2]}")

connection.close()