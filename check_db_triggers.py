import pymysql

# Check for database triggers that might affect enquiry numbers
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Check for triggers on enquiries table
cursor.execute("SHOW TRIGGERS LIKE 'enquiries'")
triggers = cursor.fetchall()

print("Triggers on enquiries table:")
for trigger in triggers:
    print(f"Trigger: {trigger[0]}, Event: {trigger[1]}, Table: {trigger[2]}")

# Check enquiries table structure
cursor.execute("DESCRIBE enquiries")
columns = cursor.fetchall()

print("\nEnquiries table structure:")
for col in columns:
    print(f"Column: {col[0]}, Type: {col[1]}, Null: {col[2]}, Key: {col[3]}, Default: {col[4]}")

# Check if there are any stored procedures
cursor.execute("SHOW PROCEDURE STATUS WHERE Db = 'ostrich_db'")
procedures = cursor.fetchall()

print(f"\nStored procedures: {len(procedures)}")
for proc in procedures:
    print(f"Procedure: {proc[1]}")

connection.close()