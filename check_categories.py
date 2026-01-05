import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Aru247899!',
        database='ostrich_db',
        port=3306,
        charset='utf8mb4'
    )
    cursor = connection.cursor()
    
    # Check table structure
    cursor.execute("DESCRIBE product_categories")
    columns = cursor.fetchall()
    print("Table structure:")
    for col in columns:
        print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]}")
    
    # Check existing data
    cursor.execute("SELECT * FROM product_categories LIMIT 5")
    data = cursor.fetchall()
    print(f"\nExisting data ({len(data)} rows):")
    for row in data:
        print(f"  {row}")
    
    connection.close()
except Exception as e:
    print(f"Error: {e}")