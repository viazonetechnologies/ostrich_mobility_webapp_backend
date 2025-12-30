import pymysql

# Local database connection
local_conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Aru247899!',
    database='ostrich_db',
    port=3306
)

# Aiven database connection
aiven_conn = pymysql.connect(
    host='mysql-ostrich-tviazone-5922.i.aivencloud.com',
    user='avnadmin',
    password='AVNS_c985UhSyW3FZhUdTmI8',
    database='defaultdb',
    port=16599,
    ssl_disabled=False
)

def migrate_table(table_name):
    local_cursor = local_conn.cursor()
    aiven_cursor = aiven_conn.cursor()
    
    # Get table structure
    local_cursor.execute(f"SHOW CREATE TABLE {table_name}")
    create_table = local_cursor.fetchone()[1]
    
    # Create table in Aiven
    try:
        aiven_cursor.execute(create_table)
        print(f"Created table: {table_name}")
    except Exception as e:
        print(f"Table {table_name} might already exist: {e}")
    
    # Copy data
    local_cursor.execute(f"SELECT * FROM {table_name}")
    rows = local_cursor.fetchall()
    
    if rows:
        # Get column count
        local_cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        col_count = len(local_cursor.fetchone())
        placeholders = ','.join(['%s'] * col_count)
        
        aiven_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
        print(f"Migrated {len(rows)} rows to {table_name}")
    
    aiven_conn.commit()

# Migrate all tables
tables = ['customers', 'enquiries', 'service_tickets', 'users', 'notifications', 
          'products', 'sales', 'regions', 'dispatches', 'customer_credentials',
          'password_reset_tokens', 'product_categories', 'sale_items', 
          'service_centers', 'service_schedules']

for table in tables:
    try:
        migrate_table(table)
    except Exception as e:
        print(f"Error migrating {table}: {e}")

local_conn.close()
aiven_conn.close()
print("Migration completed!")