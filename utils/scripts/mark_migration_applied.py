#!/usr/bin/env python
"""
Script to mark the initial sanction_for_test migration as applied
"""

import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

def mark_migration_applied():
    """Mark the initial migration as applied in Django's migration tracker"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check if django_migrations table exists
            cursor.execute("SHOW TABLES LIKE 'django_migrations'")
            if not cursor.fetchone():
                print("✗ django_migrations table not found")
                return False
            
            # Check if migration is already recorded
            cursor.execute("""
                SELECT id FROM django_migrations 
                WHERE app = 'sanction_for_test' AND name = '0001_initial'
            """)
            
            if cursor.fetchone():
                print("✓ Migration 0001_initial already marked as applied")
                return True
            
            # Insert migration record
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('sanction_for_test', '0001_initial', NOW())
            """)
            
            print("✓ Migration 0001_initial marked as applied")
            return True
            
    except Exception as e:
        print(f"✗ Error marking migration as applied: {e}")
        return False

def main():
    print("Marking sanction_for_test migration as applied...")
    print("=" * 50)
    
    if mark_migration_applied():
        print("\n✅ Success! Migration state updated.")
        print("The sanction_for_test app is now properly configured.")
    else:
        print("\n❌ Failed to update migration state.")

if __name__ == "__main__":
    main()
