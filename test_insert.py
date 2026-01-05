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
    
    # Test insert with correct columns
    cursor.execute("""
        INSERT INTO product_images (product_id, image_url, image_type, alt_text, display_order, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (1, "/static/uploads/products/test.png", "gallery", "Test image", 1, 1))
    
    connection.commit()
    print("Test record inserted successfully")
    
    # Check count
    cursor.execute("SELECT COUNT(*) FROM product_images")
    count = cursor.fetchone()[0]
    print(f"Total images now: {count}")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")