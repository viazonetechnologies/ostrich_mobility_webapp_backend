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
    
    # Update product 7 to have no main image since all images were deleted
    cursor.execute("UPDATE products SET image_url = NULL WHERE id = 7")
    connection.commit()
    
    print("Updated product 7 - removed main image URL")
    
    # Verify the update
    cursor.execute("SELECT id, name, image_url FROM products WHERE id = 7")
    product = cursor.fetchone()
    print(f"Product 7: {product[1]}, Image: {product[2]}")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")