#!/usr/bin/env python3
"""
Fix product_images table structure
"""
import pymysql

def fix_product_images_table():
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
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'product_images'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("Creating product_images table...")
            cursor.execute("""
                CREATE TABLE product_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    image_url VARCHAR(500) NOT NULL,
                    image_type VARCHAR(50) DEFAULT 'gallery',
                    alt_text VARCHAR(255),
                    display_order INT DEFAULT 1,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_product_id (product_id),
                    INDEX idx_active (is_active)
                )
            """)
            print("✅ product_images table created successfully")
        else:
            print("product_images table already exists")
            
            # Check table structure
            cursor.execute("DESCRIBE product_images")
            columns = cursor.fetchall()
            print("Current table structure:")
            for col in columns:
                print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]}")
        
        connection.commit()
        connection.close()
        print("✅ Database setup complete")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_product_images_table()