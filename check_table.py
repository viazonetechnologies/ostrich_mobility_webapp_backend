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
    
    # Check if table exists and its structure
    cursor.execute("SHOW TABLES LIKE 'product_images'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("Table exists. Structure:")
        cursor.execute("DESCRIBE product_images")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]} - {col[1]}")
    else:
        print("Table does not exist. Creating it...")
        cursor.execute("""
            CREATE TABLE product_images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                image_url VARCHAR(500) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                alt_text VARCHAR(255),
                display_order INT DEFAULT 1,
                is_primary BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        print("Table created successfully")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")