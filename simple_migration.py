import pymysql

# Database connections
local_conn = pymysql.connect(host='localhost', user='root', password='Aru247899!', database='ostrich_db', port=3306)
aiven_conn = pymysql.connect(host='mysql-ostrich-tviazone-5922.i.aivencloud.com', user='avnadmin', password='AVNS_c985UhSyW3FZhUdTmI8', database='defaultdb', port=16599, ssl_disabled=False)

local_cursor = local_conn.cursor()
aiven_cursor = aiven_conn.cursor()

# Disable foreign key checks for migration
aiven_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

def migrate_data(table_name):
    try:
        local_cursor.execute(f"SELECT * FROM {table_name}")
        rows = local_cursor.fetchall()
        
        if rows:
            # Clear existing data
            aiven_cursor.execute(f"DELETE FROM {table_name}")
            
            col_count = len(rows[0])
            placeholders = ','.join(['%s'] * col_count)
            aiven_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
            print(f"Migrated {len(rows)} rows to {table_name}")
        else:
            print(f"No data in {table_name}")
    except Exception as e:
        print(f"Error migrating {table_name}: {e}")

# Migrate in order
migrate_data('customers')
migrate_data('enquiries') 
migrate_data('service_tickets')

# Re-enable foreign key checks
aiven_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

aiven_conn.commit()
local_conn.close()
aiven_conn.close()
print("Migration completed!")