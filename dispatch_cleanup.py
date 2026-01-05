#!/usr/bin/env python3
"""
Dispatch Data Cleanup Script
Fixes common issues in dispatch data like invalid customer IDs, malformed dates, and truncated driver/vehicle info.
"""

import pymysql
from datetime import datetime, timedelta
import re

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Aru247899!',
        database='ostrich_db',
        port=3306,
        charset='utf8mb4'
    )

def fix_customer_ids():
    """Fix NULL or invalid customer IDs"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    print("Fixing customer IDs...")
    
    # Get a valid customer ID to use as default
    cursor.execute("SELECT id FROM customers ORDER BY id LIMIT 1")
    default_customer = cursor.fetchone()
    default_customer_id = default_customer[0] if default_customer else 1
    
    # Fix NULL or 0 customer IDs
    cursor.execute("""
        UPDATE dispatches 
        SET customer_id = %s 
        WHERE customer_id IS NULL OR customer_id = 0
    """, (default_customer_id,))
    
    fixed_count = cursor.rowcount
    connection.commit()
    connection.close()
    
    print(f"Fixed {fixed_count} invalid customer IDs")
    return fixed_count

def fix_dates():
    """Fix invalid dates (1970 dates, malformed GMT dates)"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    print("Fixing invalid dates...")
    
    # Fix dispatch dates that are before 2020 (likely 1970 epoch dates)
    cursor.execute("""
        UPDATE dispatches 
        SET dispatch_date = CURDATE()
        WHERE dispatch_date < '2020-01-01' OR dispatch_date IS NULL
    """)
    dispatch_fixes = cursor.rowcount
    
    # Fix estimated delivery dates
    cursor.execute("""
        UPDATE dispatches 
        SET estimated_delivery = DATE_ADD(CURDATE(), INTERVAL 2 DAY)
        WHERE estimated_delivery < '2020-01-01' OR estimated_delivery IS NULL
    """)
    delivery_fixes = cursor.rowcount
    
    connection.commit()
    connection.close()
    
    print(f"Fixed {dispatch_fixes} dispatch dates and {delivery_fixes} delivery dates")
    return dispatch_fixes + delivery_fixes

def fix_driver_vehicle_info():
    """Fix truncated or invalid driver and vehicle information"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    print("Fixing driver and vehicle information...")
    
    # Fix driver names that are too short or contain garbage
    cursor.execute("""
        UPDATE dispatches 
        SET driver_name = 'Driver TBD'
        WHERE driver_name IS NULL 
           OR driver_name = '' 
           OR LENGTH(driver_name) < 3
           OR driver_name REGEXP '[^a-zA-Z0-9 ]'
    """)
    driver_fixes = cursor.rowcount
    
    # Fix vehicle numbers that are too short or contain garbage
    cursor.execute("""
        UPDATE dispatches 
        SET vehicle_number = 'Vehicle TBD'
        WHERE vehicle_number IS NULL 
           OR vehicle_number = '' 
           OR LENGTH(vehicle_number) < 4
    """)
    vehicle_fixes = cursor.rowcount
    
    connection.commit()
    connection.close()
    
    print(f"Fixed {driver_fixes} driver names and {vehicle_fixes} vehicle numbers")
    return driver_fixes + vehicle_fixes

def fix_status_values():
    """Fix invalid status values"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    print("Fixing status values...")
    
    valid_statuses = ['pending', 'assigned', 'in_transit', 'delivered', 'cancelled']
    
    # Fix invalid statuses
    cursor.execute("""
        UPDATE dispatches 
        SET status = 'pending'
        WHERE status IS NULL 
           OR status = ''
           OR status NOT IN ('pending', 'assigned', 'in_transit', 'delivered', 'cancelled')
    """)
    
    status_fixes = cursor.rowcount
    connection.commit()
    connection.close()
    
    print(f"Fixed {status_fixes} invalid status values")
    return status_fixes

def generate_dispatch_numbers():
    """Generate dispatch numbers for records that don't have them"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    print("Generating missing dispatch numbers...")
    
    # Get records without dispatch numbers
    cursor.execute("""
        SELECT id FROM dispatches 
        WHERE dispatch_number IS NULL OR dispatch_number = ''
        ORDER BY id
    """)
    
    records = cursor.fetchall()
    fixed_count = 0
    
    for record in records:
        dispatch_id = record[0]
        dispatch_number = f"DSP{dispatch_id:06d}"
        
        cursor.execute("""
            UPDATE dispatches 
            SET dispatch_number = %s 
            WHERE id = %s
        """, (dispatch_number, dispatch_id))
        fixed_count += 1
    
    connection.commit()
    connection.close()
    
    print(f"Generated {fixed_count} dispatch numbers")
    return fixed_count

def validate_data():
    """Validate the cleaned data"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    print("\nValidating cleaned data...")
    
    # Check for remaining issues
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN customer_id IS NULL OR customer_id = 0 THEN 1 ELSE 0 END) as invalid_customers,
            SUM(CASE WHEN dispatch_date < '2020-01-01' THEN 1 ELSE 0 END) as invalid_dates,
            SUM(CASE WHEN driver_name IS NULL OR LENGTH(driver_name) < 3 THEN 1 ELSE 0 END) as invalid_drivers,
            SUM(CASE WHEN vehicle_number IS NULL OR LENGTH(vehicle_number) < 4 THEN 1 ELSE 0 END) as invalid_vehicles,
            SUM(CASE WHEN status NOT IN ('pending', 'assigned', 'in_transit', 'delivered', 'cancelled') THEN 1 ELSE 0 END) as invalid_status
        FROM dispatches
    """)
    
    validation = cursor.fetchone()
    connection.close()
    
    print(f"Total records: {validation[0]}")
    print(f"Invalid customers: {validation[1]}")
    print(f"Invalid dates: {validation[2]}")
    print(f"Invalid drivers: {validation[3]}")
    print(f"Invalid vehicles: {validation[4]}")
    print(f"Invalid status: {validation[5]}")
    
    return validation

def main():
    """Main cleanup function"""
    print("Starting dispatch data cleanup...")
    print("=" * 50)
    
    total_fixes = 0
    
    try:
        # Run all cleanup functions
        total_fixes += fix_customer_ids()
        total_fixes += fix_dates()
        total_fixes += fix_driver_vehicle_info()
        total_fixes += fix_status_values()
        total_fixes += generate_dispatch_numbers()
        
        # Validate results
        validate_data()
        
        print("=" * 50)
        print(f"Cleanup completed! Total fixes applied: {total_fixes}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()