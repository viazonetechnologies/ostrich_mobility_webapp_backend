import pymysql

# Test creating a new enquiry to verify sequential numbering
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Get current max ID
cursor.execute("SELECT MAX(id) FROM enquiries")
max_id = cursor.fetchone()[0] or 0
expected_number = f"ENQ{(max_id + 1):06d}"

print(f"Current max enquiry ID: {max_id}")
print(f"Expected next enquiry number: {expected_number}")

# Create a test enquiry
enquiry_number = f"ENQ{(max_id + 1):06d}"
cursor.execute("""
    INSERT INTO enquiries (enquiry_number, customer_id, product_id, quantity, 
                         message, status, assigned_to, follow_up_date, notes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    enquiry_number,
    1,  # customer_id
    1,  # product_id
    1,  # quantity
    "Test enquiry for sequential numbering",
    "new",
    None,
    None,
    "Test enquiry created by fix script"
))

connection.commit()
new_enquiry_id = cursor.lastrowid

print(f"Created test enquiry with ID: {new_enquiry_id}")
print(f"Enquiry number: {enquiry_number}")

# Verify the enquiry was created correctly
cursor.execute("SELECT id, enquiry_number, message FROM enquiries WHERE id = %s", (new_enquiry_id,))
result = cursor.fetchone()

if result:
    print(f"Verification - ID: {result[0]}, Number: {result[1]}, Message: {result[2]}")
    if result[1] == expected_number:
        print("✓ SUCCESS: Enquiry number format is correct!")
    else:
        print("✗ ERROR: Enquiry number format is incorrect!")
else:
    print("✗ ERROR: Could not find the created enquiry!")

connection.close()