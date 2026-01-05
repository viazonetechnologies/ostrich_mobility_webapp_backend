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
    
    # Check product_images table
    print("=== PRODUCT IMAGES TABLE ===")
    cursor.execute("SELECT COUNT(*) FROM product_images")
    count = cursor.fetchone()[0]
    print(f"Total images in database: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT id, product_id, image_url, image_type, is_active 
            FROM product_images 
            ORDER BY id DESC 
            LIMIT 10
        """)
        images = cursor.fetchall()
        
        print("\nRecent images:")
        for img in images:
            print(f"  ID: {img[0]}, Product: {img[1]}, URL: {img[2]}, Type: {img[3]}, Active: {img[4]}")
    
    # Check products table
    print("\n=== PRODUCTS TABLE ===")
    cursor.execute("SELECT id, name, image_url FROM products LIMIT 10")
    products = cursor.fetchall()
    
    print("Products:")
    for prod in products:
        print(f"  ID: {prod[0]}, Name: {prod[1]}, Image: {prod[2]}")
    
    connection.close()
    
except Exception as e:
    print(f"Database error: {e}")