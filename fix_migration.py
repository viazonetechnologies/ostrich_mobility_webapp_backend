import pymysql

# Database connections
local_conn = pymysql.connect(host='localhost', user='root', password='Aru247899!', database='ostrich_db', port=3306)
aiven_conn = pymysql.connect(host='mysql-ostrich-tviazone-5922.i.aivencloud.com', user='avnadmin', password='AVNS_c985UhSyW3FZhUdTmI8', database='defaultdb', port=16599, ssl_disabled=False)

local_cursor = local_conn.cursor()
aiven_cursor = aiven_conn.cursor()

# Disable foreign key checks
aiven_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

# Drop and recreate customers table
aiven_cursor.execute("DROP TABLE IF EXISTS customers")
local_cursor.execute("SHOW CREATE TABLE customers")
create_customers = local_cursor.fetchone()[1]
aiven_cursor.execute(create_customers)
print("Recreated customers table")

# Drop and recreate enquiries table  
aiven_cursor.execute("DROP TABLE IF EXISTS enquiries")
local_cursor.execute("SHOW CREATE TABLE enquiries")
create_enquiries = local_cursor.fetchone()[1]
aiven_cursor.execute(create_enquiries)
print("Recreated enquiries table")

# Drop and recreate service_tickets table
aiven_cursor.execute("DROP TABLE IF EXISTS service_tickets")
local_cursor.execute("SHOW CREATE TABLE service_tickets")
create_service_tickets = local_cursor.fetchone()[1]
aiven_cursor.execute(create_service_tickets)
print("Recreated service_tickets table")

# Re-enable foreign key checks
aiven_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

# Migrate data
def migrate_data(table_name):
    local_cursor.execute(f"SELECT * FROM {table_name}")
    rows = local_cursor.fetchall()
    
    if rows:
        col_count = len(rows[0])
        placeholders = ','.join(['%s'] * col_count)
        aiven_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
        print(f"Migrated {len(rows)} rows to {table_name}")

migrate_data('customers')
migrate_data('enquiries') 
migrate_data('service_tickets')

aiven_conn.commit()
local_conn.close()
aiven_conn.close()
print("Migration completed successfully!")