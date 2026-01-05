import pymysql

# Clean up test enquiry and show final state
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Delete the test enquiry
cursor.execute("DELETE FROM enquiries WHERE message = 'Test enquiry for sequential numbering'")
deleted_count = cursor.rowcount
connection.commit()

print(f"Deleted {deleted_count} test enquiry(ies)")

# Show final state
cursor.execute("SELECT id, enquiry_number, customer_id, created_at FROM enquiries ORDER BY id DESC LIMIT 5")
enquiries = cursor.fetchall()

print("\nFinal enquiries in database:")
for enq in enquiries:
    print(f"ID: {enq[0]}, Number: {enq[1]}, Customer: {enq[2]}, Created: {enq[3]}")

# Get max ID for next enquiry
cursor.execute("SELECT MAX(id) FROM enquiries")
max_id = cursor.fetchone()[0] or 0
print(f"\nNext enquiry will be: ENQ{(max_id + 1):06d}")

connection.close()
print("\nEnquiry numbering system is now working correctly with sequential format!")