#!/usr/bin/env python
"""
Manual table creation script for sanction_for_test app
This script creates the database tables directly using Django's schema editor
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection
from django.core.management.color import no_style

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

# Import models after Django setup
try:
    from sanction_for_test.models import (
        SanctionForTestForm, SanctionFormComment, 
        SanctionFormAuditLog, SanctionFormAttachment
    )
    print("✓ Models imported successfully")
except Exception as e:
    print(f"✗ Model import failed: {e}")
    sys.exit(1)

def create_tables():
    """Create tables manually using Django's schema editor"""
    try:
        with connection.schema_editor() as schema_editor:
            print("Creating tables...")
            
            # Create SanctionForTestForm table
            print("  Creating SanctionForTestForm table...")
            schema_editor.create_model(SanctionForTestForm)
            print("  ✓ SanctionForTestForm table created")
            
            # Create SanctionFormComment table
            print("  Creating SanctionFormComment table...")
            schema_editor.create_model(SanctionFormComment)
            print("  ✓ SanctionFormComment table created")
            
            # Create SanctionFormAuditLog table
            print("  Creating SanctionFormAuditLog table...")
            schema_editor.create_model(SanctionFormAuditLog)
            print("  ✓ SanctionFormAuditLog table created")
            
            # Create SanctionFormAttachment table
            print("  Creating SanctionFormAttachment table...")
            schema_editor.create_model(SanctionFormAttachment)
            print("  ✓ SanctionFormAttachment table created")
            
        print("✓ All tables created successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

def check_tables():
    """Check if tables exist"""
    try:
        with connection.cursor() as cursor:
            # Check if sanction_for_test tables exist
            cursor.execute("SHOW TABLES LIKE 'sanction_for_test%'")
            tables = cursor.fetchall()
            
            if tables:
                print("Found sanction_for_test tables:")
                for table in tables:
                    print(f"  - {table[0]}")
                return True
            else:
                print("No sanction_for_test tables found")
                return False
                
    except Exception as e:
        print(f"✗ Error checking tables: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                print("✓ Database connection successful")
                return True
            else:
                print("✗ Database connection test failed")
                return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False

def main():
    print("Manual Table Creation for Sanction For Test")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("Cannot proceed without database connection")
        return
    
    # Check if tables already exist
    if check_tables():
        print("Tables already exist. No action needed.")
        return
    
    # Create tables
    if create_tables():
        print("\n✅ Success! Tables created successfully.")
        print("You can now use the sanction_for_test application.")
        
        # Verify tables were created
        print("\nVerifying tables...")
        check_tables()
    else:
        print("\n❌ Failed to create tables.")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
