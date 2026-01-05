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
    
    # Clear product_images table
    cursor.execute("TRUNCATE TABLE product_images")
    print("Truncated product_images table")
    
    # Clear main product images
    cursor.execute("UPDATE products SET image_url = NULL")
    print("Cleared all main product images")
    
    connection.commit()
    
    # Verify both are empty/cleared
    cursor.execute("SELECT COUNT(*) FROM product_images")
    images_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE image_url IS NOT NULL")
    products_with_images = cursor.fetchone()[0]
    
    print(f"Product images count: {images_count}")
    print(f"Products with images: {products_with_images}")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")