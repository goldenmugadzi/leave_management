#!/usr/bin/env python
"""
Add missing columns to existing tables
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.append('.')
django.setup()

from django.db import connection

def add_missing_columns():
    """Add missing columns to existing tables"""
    cursor = connection.cursor()
    
    # List of columns to add with their SQL
    column_additions = [
        # FaultLocatorTeam table
        ("fault_locator_faultlocatorteam", "team_leader_id", "ALTER TABLE fault_locator_faultlocatorteam ADD COLUMN team_leader_id bigint DEFAULT NULL;"),
        ("fault_locator_faultlocatorteam", "created_at", "ALTER TABLE fault_locator_faultlocatorteam ADD COLUMN created_at datetime(6) NOT NULL DEFAULT NOW(6);"),
        ("fault_locator_faultlocatorteam", "created_by_id", "ALTER TABLE fault_locator_faultlocatorteam ADD COLUMN created_by_id bigint DEFAULT NULL;"),
        
        # FaultLocatorDevice table
        ("fault_locator_faultlocatordevice", "created_at", "ALTER TABLE fault_locator_faultlocatordevice ADD COLUMN created_at datetime(6) NOT NULL DEFAULT NOW(6);"),
        ("fault_locator_faultlocatordevice", "created_by_id", "ALTER TABLE fault_locator_faultlocatordevice ADD COLUMN created_by_id bigint DEFAULT NULL;"),
        ("fault_locator_faultlocatordevice", "status", "ALTER TABLE fault_locator_faultlocatordevice ADD COLUMN status varchar(20) NOT NULL DEFAULT 'available';"),
        
        # FaultLocatorDeviceAssignment table
        ("fault_locator_faultlocatordeviceassignment", "assigned_by_id", "ALTER TABLE fault_locator_faultlocatordeviceassignment ADD COLUMN assigned_by_id bigint DEFAULT NULL;"),
        ("fault_locator_faultlocatordeviceassignment", "notes", "ALTER TABLE fault_locator_faultlocatordeviceassignment ADD COLUMN notes longtext NOT NULL DEFAULT '';"),
        
        # Fault table
        ("fault_locator_fault", "foreperson_notes", "ALTER TABLE fault_locator_fault ADD COLUMN foreperson_notes longtext NOT NULL DEFAULT '';"),
        ("fault_locator_fault", "team_leader_notes", "ALTER TABLE fault_locator_fault ADD COLUMN team_leader_notes longtext NOT NULL DEFAULT '';"),
        ("fault_locator_fault", "location_details", "ALTER TABLE fault_locator_fault ADD COLUMN location_details longtext NOT NULL DEFAULT '';"),
        ("fault_locator_fault", "reported_by_id", "ALTER TABLE fault_locator_fault ADD COLUMN reported_by_id bigint DEFAULT NULL;"),
        ("fault_locator_fault", "verified_by_id", "ALTER TABLE fault_locator_fault ADD COLUMN verified_by_id bigint DEFAULT NULL;"),
        ("fault_locator_fault", "verified_at", "ALTER TABLE fault_locator_fault ADD COLUMN verified_at datetime(6) DEFAULT NULL;"),
        
        # FaultAssignment table
        ("fault_locator_faultassignment", "actual_completion", "ALTER TABLE fault_locator_faultassignment ADD COLUMN actual_completion datetime(6) DEFAULT NULL;"),
        ("fault_locator_faultassignment", "assigned_by_id", "ALTER TABLE fault_locator_faultassignment ADD COLUMN assigned_by_id bigint DEFAULT NULL;"),
        ("fault_locator_faultassignment", "estimated_completion", "ALTER TABLE fault_locator_faultassignment ADD COLUMN estimated_completion datetime(6) DEFAULT NULL;"),
        ("fault_locator_faultassignment", "located_by_id", "ALTER TABLE fault_locator_faultassignment ADD COLUMN located_by_id bigint DEFAULT NULL;"),
        ("fault_locator_faultassignment", "work_notes", "ALTER TABLE fault_locator_faultassignment ADD COLUMN work_notes longtext NOT NULL DEFAULT '';"),
        ("fault_locator_faultassignment", "work_started_at", "ALTER TABLE fault_locator_faultassignment ADD COLUMN work_started_at datetime(6) DEFAULT NULL;"),
    ]
    
    def column_exists(table_name, column_name):
        """Check if a column exists in a table"""
        cursor.execute(f"DESCRIBE {table_name}")
        columns = [row[0] for row in cursor.fetchall()]
        return column_name in columns
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for table_name, column_name, sql_statement in column_additions:
        try:
            if column_exists(table_name, column_name):
                print(f"✓ Column {table_name}.{column_name} already exists")
                skip_count += 1
            else:
                cursor.execute(sql_statement)
                print(f"✓ Added column {table_name}.{column_name}")
                success_count += 1
        except Exception as e:
            print(f"✗ Error adding {table_name}.{column_name}: {e}")
            error_count += 1
    
    print(f"\nSummary: {success_count} added, {skip_count} skipped, {error_count} errors")
    return error_count == 0

if __name__ == "__main__":
    success = add_missing_columns()
    if success:
        print("\nAll missing columns processed successfully!")
        print("The fault locator should now work properly.")
    else:
        print("\nSome errors occurred while adding columns.")
