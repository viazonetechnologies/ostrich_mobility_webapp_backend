import pymysql

# Database connections
local_conn = pymysql.connect(host='localhost', user='root', password='Aru247899!', database='ostrich_db', port=3306)
aiven_conn = pymysql.connect(host='mysql-ostrich-tviazone-5922.i.aivencloud.com', user='avnadmin', password='AVNS_c985UhSyW3FZhUdTmI8', database='defaultdb', port=16599, ssl_disabled=False)

local_cursor = local_conn.cursor()
aiven_cursor = aiven_conn.cursor()

# Disable foreign key checks
aiven_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

def migrate_table_full(table_name):
    try:
        # Get table structure
        local_cursor.execute(f"SHOW CREATE TABLE {table_name}")
        create_table = local_cursor.fetchone()[1]
        
        # Drop and recreate table
        aiven_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        aiven_cursor.execute(create_table)
        print(f"Created table: {table_name}")
        
        # Copy data
        local_cursor.execute(f"SELECT * FROM {table_name}")
        rows = local_cursor.fetchall()
        
        if rows:
            col_count = len(rows[0])
            placeholders = ','.join(['%s'] * col_count)
            aiven_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
            print(f"Migrated {len(rows)} rows to {table_name}")
        else:
            print(f"No data in {table_name}")
            
    except Exception as e:
        print(f"Error migrating {table_name}: {e}")

# Migrate missing tables
missing_tables = ['products', 'sales', 'dispatches', 'customer_credentials', 'sale_items', 'service_schedules']

for table in missing_tables:
    migrate_table_full(table)

# Re-enable foreign key checks
aiven_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

aiven_conn.commit()
local_conn.close()
aiven_conn.close()
print("Missing tables migration completed!")