#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.db import connection

def add_fault_columns():
    cursor = connection.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("DESCRIBE fault_locator_fault")
        existing_columns = [col[0] for col in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add voltage column if it doesn't exist
        if 'voltage' not in existing_columns:
            cursor.execute("ALTER TABLE fault_locator_fault ADD COLUMN voltage VARCHAR(10) NULL")
            print("✓ Added voltage column")
        else:
            print("- voltage column already exists")
            
        # Add backfeed column if it doesn't exist
        if 'backfeed' not in existing_columns:
            cursor.execute("ALTER TABLE fault_locator_fault ADD COLUMN backfeed TINYINT(1) NOT NULL DEFAULT 0")
            print("✓ Added backfeed column")
        else:
            print("- backfeed column already exists")
            
        # Add clients_affected column if it doesn't exist
        if 'clients_affected' not in existing_columns:
            cursor.execute("ALTER TABLE fault_locator_fault ADD COLUMN clients_affected INTEGER UNSIGNED NULL")
            print("✓ Added clients_affected column")
        else:
            print("- clients_affected column already exists")
            
        # Verify the changes
        cursor.execute("DESCRIBE fault_locator_fault")
        new_columns = [col[0] for col in cursor.fetchall()]
        print(f"\nUpdated columns: {new_columns}")
        
        print("\n🎉 Database update completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    add_fault_columns()
