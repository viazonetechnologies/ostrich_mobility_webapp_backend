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
    
    # Check Product 4 specifically
    print("=== PRODUCT 4 (MCCB 100A) IMAGES ===")
    cursor.execute("""
        SELECT id, product_id, image_url, image_type, alt_text, display_order, is_active, created_at
        FROM product_images 
        WHERE product_id = 4
        ORDER BY display_order, created_at
    """)
    
    images = cursor.fetchall()
    print(f"Found {len(images)} images for Product 4:")
    
    for img in images:
        print(f"  ID: {img[0]}, URL: {img[2]}, Active: {img[6]}")
    
    # Check main product record
    cursor.execute("SELECT id, name, image_url FROM products WHERE id = 4")
    product = cursor.fetchone()
    print(f"\nProduct 4: {product[1]}")
    print(f"Main image: {product[2]}")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")