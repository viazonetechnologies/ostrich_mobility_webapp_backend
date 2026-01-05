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
    
    # Add sample categories
    categories = [
        (1, 'Mobility Equipment', 'Wheelchairs and mobility aids'),
        (2, 'Motors', 'Electric and manual motors'),
        (3, 'Electrical Components', 'MCBs, MCCBs, and electrical parts'),
        (4, 'Cables & Wiring', 'Electrical cables and wiring solutions')
    ]
    
    for cat_id, name, desc in categories:
        cursor.execute("""
            INSERT IGNORE INTO product_categories (id, name, description, is_active) 
            VALUES (%s, %s, %s, 1)
        """, (cat_id, name, desc))
    
    # Update products with categories
    cursor.execute("UPDATE products SET category_id = 1 WHERE name LIKE '%chair%'")
    cursor.execute("UPDATE products SET category_id = 2 WHERE name LIKE '%Motor%'")
    cursor.execute("UPDATE products SET category_id = 3 WHERE name LIKE '%MCB%' OR name LIKE '%MCCB%' OR name LIKE '%Panel%' OR name LIKE '%Contactor%'")
    cursor.execute("UPDATE products SET category_id = 4 WHERE name LIKE '%Cable%'")
    
    connection.commit()
    print("Categories added successfully!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if connection:
        connection.close()