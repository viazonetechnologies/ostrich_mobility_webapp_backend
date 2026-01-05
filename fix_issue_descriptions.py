#!/usr/bin/env python3
import pymysql

def fix_issue_descriptions():
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
        
        # Update short/meaningless issue descriptions with proper ones
        issue_updates = [
            ("fd", "Motor not starting - requires inspection"),
            ("az", "Wheel alignment issue - needs adjustment"),
            ("hl", "Battery not charging properly"),
            ("dh", "Control panel malfunction"),
            ("sdc", "Brake system maintenance required"),
            ("u", "General maintenance and inspection"),
            ("ga", "Electrical wiring check needed"),
            ("svh", "Seat adjustment mechanism repair")
        ]
        
        for old_desc, new_desc in issue_updates:
            cursor.execute("""
                UPDATE service_tickets 
                SET issue_description = %s 
                WHERE issue_description = %s
            """, (new_desc, old_desc))
            
            if cursor.rowcount > 0:
                print(f"Updated '{old_desc}' to '{new_desc}' ({cursor.rowcount} records)")
        
        # Fix any remaining very short descriptions
        cursor.execute("""
            UPDATE service_tickets 
            SET issue_description = 'Service maintenance required - please provide details'
            WHERE LENGTH(issue_description) < 5
        """)
        
        short_fixed = cursor.rowcount
        print(f"Fixed {short_fixed} very short descriptions")
        
        connection.commit()
        
        # Show updated data
        print("\n=== UPDATED ISSUE DESCRIPTIONS ===")
        cursor.execute("""
            SELECT id, ticket_number, issue_description, priority, status
            FROM service_tickets 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        tickets = cursor.fetchall()
        for ticket in tickets:
            print(f"TKT{ticket[0]:06d}: {ticket[2]} [{ticket[3]}/{ticket[4]}]")
        
        connection.close()
        print("\nIssue descriptions fixed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_issue_descriptions()