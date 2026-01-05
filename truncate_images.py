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
    
    # Truncate product_images table
    cursor.execute("TRUNCATE TABLE product_images")
    connection.commit()
    
    print("Successfully truncated product_images table")
    
    # Verify it's empty
    cursor.execute("SELECT COUNT(*) FROM product_images")
    count = cursor.fetchone()[0]
    print(f"Product images count after truncate: {count}")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")