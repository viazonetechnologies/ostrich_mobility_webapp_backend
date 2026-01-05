import pymysql

# Update service_tickets table structure
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Check current table structure
cursor.execute("DESCRIBE service_tickets")
columns = cursor.fetchall()
print("Current service_tickets table structure:")
for col in columns:
    print(f"Column: {col[0]}, Type: {col[1]}")

# Check if product_id column exists
has_product_id = any(col[0] == 'product_id' for col in columns)
has_product_serial = any(col[0] == 'product_serial_number' for col in columns)

print(f"\nHas product_id: {has_product_id}")
print(f"Has product_serial_number: {has_product_serial}")

if not has_product_id and has_product_serial:
    print("\nAdding product_id column...")
    cursor.execute("ALTER TABLE service_tickets ADD COLUMN product_id INT AFTER customer_id")
    
    # Set some default product_id values for existing tickets
    cursor.execute("UPDATE service_tickets SET product_id = 1 WHERE product_id IS NULL")
    
    connection.commit()
    print("Added product_id column and set default values")

# Show updated structure
cursor.execute("DESCRIBE service_tickets")
columns = cursor.fetchall()
print("\nUpdated service_tickets table structure:")
for col in columns:
    print(f"Column: {col[0]}, Type: {col[1]}")

connection.close()
print("\nService tickets table updated successfully!")