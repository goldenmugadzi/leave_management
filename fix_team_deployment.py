#!/usr/bin/env python
"""
Create TeamDeployment table manually
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.append('.')
django.setup()

from django.db import connection

def create_team_deployment_table():
    """Create TeamDeployment table without foreign key constraints first"""
    cursor = connection.cursor()
    
    # Create TeamDeployment table without constraints
    deployment_table_sql = """
    CREATE TABLE IF NOT EXISTS `fault_locator_teamdeployment` (
        `id` bigint NOT NULL AUTO_INCREMENT,
        `deployed_at` datetime(6) NOT NULL,
        `recalled_at` datetime(6) DEFAULT NULL,
        `deployment_notes` longtext NOT NULL,
        `recall_notes` longtext NOT NULL,
        `deployed_by_id` bigint NOT NULL,
        `depot_id` bigint NOT NULL,
        `recalled_by_id` bigint DEFAULT NULL,
        `team_id` bigint NOT NULL,
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
    """
    
    try:
        print("Creating TeamDeployment table...")
        cursor.execute(deployment_table_sql)
        print("✓ TeamDeployment table created successfully")
        
        # Add the missing fields to existing tables
        add_fields_sql = [
            "ALTER TABLE fault_locator_fault ADD COLUMN IF NOT EXISTS foreperson_notes longtext NOT NULL DEFAULT '';",
            "ALTER TABLE fault_locator_fault ADD COLUMN IF NOT EXISTS team_leader_notes longtext NOT NULL DEFAULT '';",
            "ALTER TABLE fault_locator_fault ADD COLUMN IF NOT EXISTS location_details longtext NOT NULL DEFAULT '';",
            "ALTER TABLE fault_locator_fault ADD COLUMN IF NOT EXISTS reported_by_id bigint DEFAULT NULL;",
            "ALTER TABLE fault_locator_fault ADD COLUMN IF NOT EXISTS verified_by_id bigint DEFAULT NULL;",
            "ALTER TABLE fault_locator_fault ADD COLUMN IF NOT EXISTS verified_at datetime(6) DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultassignment ADD COLUMN IF NOT EXISTS actual_completion datetime(6) DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultassignment ADD COLUMN IF NOT EXISTS assigned_by_id bigint DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultassignment ADD COLUMN IF NOT EXISTS estimated_completion datetime(6) DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultassignment ADD COLUMN IF NOT EXISTS located_by_id bigint DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultassignment ADD COLUMN IF NOT EXISTS work_notes longtext NOT NULL DEFAULT '';",
            "ALTER TABLE fault_locator_faultassignment ADD COLUMN IF NOT EXISTS work_started_at datetime(6) DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultlocatordevice ADD COLUMN IF NOT EXISTS created_at datetime(6) NOT NULL DEFAULT NOW();",
            "ALTER TABLE fault_locator_faultlocatordevice ADD COLUMN IF NOT EXISTS created_by_id bigint DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultlocatordevice ADD COLUMN IF NOT EXISTS status varchar(20) NOT NULL DEFAULT 'available';",
            "ALTER TABLE fault_locator_faultlocatordeviceassignment ADD COLUMN IF NOT EXISTS assigned_by_id bigint DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultlocatordeviceassignment ADD COLUMN IF NOT EXISTS notes longtext NOT NULL DEFAULT '';",
            "ALTER TABLE fault_locator_faultlocatorteam ADD COLUMN IF NOT EXISTS created_at datetime(6) NOT NULL DEFAULT NOW();",
            "ALTER TABLE fault_locator_faultlocatorteam ADD COLUMN IF NOT EXISTS created_by_id bigint DEFAULT NULL;",
            "ALTER TABLE fault_locator_faultlocatorteam ADD COLUMN IF NOT EXISTS team_leader_id bigint DEFAULT NULL;",
        ]
        
        for sql in add_fields_sql:
            try:
                cursor.execute(sql)
                print(f"✓ Added field: {sql[:50]}...")
            except Exception as e:
                if "Duplicate column name" not in str(e):
                    print(f"Warning: {e}")
        
        print("All missing fields added successfully!")
        
    except Exception as e:
        print(f"Error creating table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_team_deployment_table()
    if success:
        print("\nDatabase structure fixed successfully!")
        print("You can now run: python manage.py runserver")
    else:
        print("\nFailed to fix database structure.")
