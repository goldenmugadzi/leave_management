"""
Virament Database Schema Fix
Creates migration to add missing 'grade' column to UserProfile model
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

try:
    django.setup()
    print("✅ Django environment configured successfully")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from django.core.management import execute_from_command_line
from django.db import models
from it.users.models import UserProfile


def check_current_schema():
    """Check current UserProfile model fields"""
    print("\n🔍 CHECKING CURRENT USERPROFILE SCHEMA...")
    print("=" * 60)

    # Get all fields from UserProfile model
    fields = [field.name for field in UserProfile._meta.fields]
    print(f"Current UserProfile fields: {fields}")

    # Check if grade field exists
    if 'grade' in fields:
        print("✅ 'grade' field already exists in UserProfile model")
        return True
    else:
        print("❌ 'grade' field is missing from UserProfile model")
        return False


def create_migration():
    """Create migration to add grade field"""
    print("\n🔧 CREATING MIGRATION FOR GRADE FIELD...")
    print("=" * 60)

    try:
        # Create migration for the users app
        execute_from_command_line(['manage.py', 'makemigrations', 'users'])
        print("✅ Migration created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create migration: {e}")
        return False


def show_migration_content():
    """Show the content of the created migration"""
    print("\n📄 MIGRATION CONTENT...")
    print("=" * 60)

    # Look for the latest migration file in users/migrations/
    migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'it', 'users', 'migrations')

    if not os.path.exists(migrations_dir):
        print("❌ Migrations directory not found")
        return False

    # Find the latest migration file
    migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py') and f != '__init__.py']
    if not migration_files:
        print("❌ No migration files found")
        return False

    # Sort by name to get the latest
    migration_files.sort()
    latest_migration = migration_files[-1]

    migration_path = os.path.join(migrations_dir, latest_migration)
    print(f"Latest migration file: {latest_migration}")

    try:
        with open(migration_path, 'r') as f:
            content = f.read()
            print("\nMigration content:")
            print("-" * 40)
            print(content)
            print("-" * 40)
        return True
    except Exception as e:
        print(f"❌ Failed to read migration file: {e}")
        return False


def run_migration():
    """Run the migration to apply changes"""
    print("\n🚀 RUNNING MIGRATION...")
    print("=" * 60)

    try:
        execute_from_command_line(['manage.py', 'migrate', 'users'])
        print("✅ Migration applied successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to apply migration: {e}")
        return False


def verify_schema_fix():
    """Verify that the grade field has been added"""
    print("\n✅ VERIFYING SCHEMA FIX...")
    print("=" * 60)

    # Check if grade field now exists
    fields = [field.name for field in UserProfile._meta.fields]
    print(f"Updated UserProfile fields: {fields}")

    if 'grade' in fields:
        print("✅ SUCCESS: 'grade' field has been added to UserProfile model")
        return True
    else:
        print("❌ FAILURE: 'grade' field is still missing from UserProfile model")
        return False


def main():
    """Main function to fix database schema"""
    print("=" * 80)
    print("🔧 VIRAMENT DATABASE SCHEMA FIX")
    print("=" * 80)
    print("Adding missing 'grade' column to UserProfile model")
    print("=" * 80)

    # Step 1: Check current schema
    if check_current_schema():
        print("\n✅ Schema is already correct - no action needed")
        return True

    # Step 2: Create migration
    if not create_migration():
        print("\n❌ Failed to create migration")
        return False

    # Step 3: Show migration content
    show_migration_content()

    # Step 4: Ask user to review and confirm
    print("\n⚠️  REVIEW REQUIRED:")
    print("   Please review the migration content above.")
    print("   The migration will add a 'grade' field to the UserProfile model.")
    response = input("\nDo you want to proceed with applying this migration? (y/N): ").strip().lower()

    if response != 'y':
        print("Migration cancelled by user")
        return False

    # Step 5: Run migration
    if not run_migration():
        print("\n❌ Failed to apply migration")
        return False

    # Step 6: Verify fix
    if verify_schema_fix():
        print("\n🎉 DATABASE SCHEMA FIX COMPLETED SUCCESSFULLY!")
        print("\n✅ You can now run the full virament workflow tests")
        print("   Run: python manage.py test test_virament_real_workflow.ViramentRealWorkflowTestCase")
        return True
    else:
        print("\n❌ Schema fix verification failed")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)