import pymysql

# Add multiple test images for product 1
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# Add multiple images for product 1
test_images = [
    (1, '/static/uploads/products/test1.jpg', 'gallery', 'Test Image 1', 1, 1),
    (1, '/static/uploads/products/test2.jpg', 'gallery', 'Test Image 2', 2, 1),
    (1, '/static/uploads/products/test3.jpg', 'gallery', 'Test Image 3', 3, 1),
]

for product_id, image_url, image_type, alt_text, display_order, is_active in test_images:
    cursor.execute("""
        INSERT INTO product_images (product_id, image_url, image_type, alt_text, display_order, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (product_id, image_url, image_type, alt_text, display_order, is_active))

connection.commit()
connection.close()
print("Test images added successfully")