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
    
    print("=== SALES TABLE STRUCTURE ===")
    cursor.execute("DESCRIBE sales")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} - Null: {row[2]} - Default: {row[4]}")
    
    print("\n=== SALE_ITEMS TABLE STRUCTURE ===")
    cursor.execute("DESCRIBE sale_items")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} - Null: {row[2]} - Default: {row[4]}")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")