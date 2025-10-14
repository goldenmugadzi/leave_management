#!/usr/bin/env python3
"""
Script to create and apply database migration for new fault fields
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
    django.setup()

def create_migration():
    """Create database migration for fault locator app"""
    print("Creating migration for fault_locator app...")
    try:
        execute_from_command_line([
            'manage.py', 
            'makemigrations', 
            'fault_locator', 
            '--name=add_fault_technical_fields'
        ])
        print("✅ Migration created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating migration: {e}")
        return False

def apply_migration():
    """Apply the migration"""
    print("Applying migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migration applied successfully!")
        return True
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        return False

def main():
    print("=" * 60)
    print("FAULT LOCATOR TECHNICAL FIELDS MIGRATION")
    print("=" * 60)
    print("Adding voltage, backfeed, and clients_affected fields to Fault model")
    print()
    
    setup_django()
    
    # Create migration
    if create_migration():
        print()
        # Apply migration
        if apply_migration():
            print()
            print("=" * 60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("New fields added to Fault model:")
            print("- voltage: Choices field (0.4kV to 400kV)")
            print("- backfeed: Boolean field (default: False)")
            print("- clients_affected: Positive integer field")
            print()
            print("The forms and templates have been updated to include these fields.")
        else:
            print()
            print("=" * 60)
            print("MIGRATION CREATION SUCCESSFUL BUT APPLICATION FAILED")
            print("=" * 60)
            print("Please run 'python manage.py migrate' manually")
    else:
        print()
        print("=" * 60)
        print("MIGRATION CREATION FAILED")
        print("=" * 60)
        print("Please check the error above and try again")

if __name__ == "__main__":
    main()
