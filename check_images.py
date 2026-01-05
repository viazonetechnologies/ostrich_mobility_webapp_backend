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
    
    # Check if product_images table exists
    cursor.execute("SHOW TABLES LIKE 'product_images'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        cursor.execute("SELECT COUNT(*) FROM product_images")
        count = cursor.fetchone()[0]
        print(f"Total images in product_images table: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, product_id, image_url, image_type, created_at FROM product_images ORDER BY created_at DESC LIMIT 5")
            images = cursor.fetchall()
            print("\nRecent images:")
            for img in images:
                print(f"ID: {img[0]}, Product ID: {img[1]}, URL: {img[2]}, Type: {img[3]}, Created: {img[4]}")
        else:
            print("No images found in the table")
    else:
        print("product_images table does not exist")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")