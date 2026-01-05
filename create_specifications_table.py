import pymysql

# Create product_specifications table
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_specifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        category VARCHAR(100) NOT NULL,
        feature_name VARCHAR(100) NOT NULL,
        feature_value VARCHAR(255) NOT NULL,
        display_order INT DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
""")

connection.commit()
connection.close()
print("product_specifications table created successfully")