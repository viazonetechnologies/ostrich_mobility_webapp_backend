import pymysql

# Database connections
local_conn = pymysql.connect(host='localhost', user='root', password='Aru247899!', database='ostrich_db', port=3306)
aiven_conn = pymysql.connect(host='mysql-ostrich-tviazone-5922.i.aivencloud.com', user='avnadmin', password='AVNS_c985UhSyW3FZhUdTmI8', database='defaultdb', port=16599, ssl_disabled=False)

def migrate_table_data_only(table_name):
    local_cursor = local_conn.cursor()
    aiven_cursor = aiven_conn.cursor()
    
    # Copy data only (tables already created)
    local_cursor.execute(f"SELECT * FROM {table_name}")
    rows = local_cursor.fetchall()
    
    if rows:
        col_count = len(rows[0])
        placeholders = ','.join(['%s'] * col_count)
        aiven_cursor.executemany(f"INSERT IGNORE INTO {table_name} VALUES ({placeholders})", rows)
        print(f"Migrated {len(rows)} rows to {table_name}")
    
    aiven_conn.commit()

# Create remaining tables in dependency order
aiven_cursor = aiven_conn.cursor()

# Create customers table
aiven_cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create other essential tables
aiven_cursor.execute("""
CREATE TABLE IF NOT EXISTS enquiries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    message TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
""")

aiven_cursor.execute("""
CREATE TABLE IF NOT EXISTS service_tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    title VARCHAR(255),
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
""")

aiven_conn.commit()
print("Created essential tables")

# Now migrate data for tables that exist
try:
    migrate_table_data_only('customers')
except Exception as e:
    print(f"Error migrating customers: {e}")

try:
    migrate_table_data_only('enquiries')
except Exception as e:
    print(f"Error migrating enquiries: {e}")

try:
    migrate_table_data_only('service_tickets')
except Exception as e:
    print(f"Error migrating service_tickets: {e}")

local_conn.close()
aiven_conn.close()
print("Migration completed!")