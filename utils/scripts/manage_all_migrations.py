#!/usr/bin/env python
"""
Comprehensive Django Migration Management Script
This script automates the entire migration process for all Django apps in the project.
"""

import os
import sys
import django
from pathlib import Path
import subprocess
import time

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.conf import settings
from django.apps import apps
from django.core.management import execute_from_command_line
from django.db import connection

def get_all_apps():
    """Get all installed apps that should have migrations."""
    installed_apps = []
    
    for app_config in apps.get_app_configs():
        app_name = app_config.name
        # Skip Django built-in apps that don't need custom migrations
        if app_name.startswith('django.contrib.'):
            continue
        installed_apps.append(app_name)
    
    return installed_apps

def create_migration_folders():
    """Create migration folders for apps that don't have them."""
    print("🔍 Checking for missing migration folders...")
    
    for app_config in apps.get_app_configs():
        app_name = app_config.name
        app_path = Path(app_config.path)
        migrations_path = app_path / 'migrations'
        
        # Skip Django built-in apps
        if app_name.startswith('django.contrib.'):
            continue
            
        if not migrations_path.exists():
            print(f"📁 Creating migration folder for {app_name}")
            migrations_path.mkdir(exist_ok=True)
            
            # Create __init__.py file
            init_file = migrations_path / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                print(f"   ✅ Created __init__.py for {app_name}")

def check_app_has_models(app_name):
    """Check if an app has models that need migrations."""
    try:
        app_config = apps.get_app_config(app_name.split('.')[-1])
        models_module = app_config.models_module
        if models_module:
            # Check if there are any models defined
            from django.db import models
            model_list = [obj for obj in models_module.__dict__.values() 
                         if isinstance(obj, type) and issubclass(obj, models.Model) 
                         and obj._meta.app_label == app_config.label]
            return len(model_list) > 0
    except Exception as e:
        print(f"⚠️  Warning checking models for {app_name}: {e}")
    return False

def run_makemigrations():
    """Run makemigrations for all apps."""
    print("\n🔄 Running makemigrations for all apps...")
    
    try:
        # Run makemigrations without specifying apps (will do all)
        result = subprocess.run([
            sys.executable, 'manage.py', 'makemigrations'
        ], capture_output=True, text=True, cwd=BASE_DIR)
        
        if result.returncode == 0:
            print("✅ makemigrations completed successfully")
            if result.stdout:
                print("📝 Output:")
                print(result.stdout)
        else:
            print("❌ makemigrations failed")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running makemigrations: {e}")
        return False
    
    return True

def run_migrate():
    """Run migrate for all apps."""
    print("\n🚀 Running migrate for all apps...")
    
    try:
        # Run migrate without specifying apps (will do all)
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], capture_output=True, text=True, cwd=BASE_DIR)
        
        if result.returncode == 0:
            print("✅ migrate completed successfully")
            if result.stdout:
                print("📝 Output:")
                print(result.stdout)
        else:
            print("❌ migrate failed")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migrate: {e}")
        return False
    
    return True

def show_migration_status():
    """Show current migration status."""
    print("\n📊 Current Migration Status:")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'showmigrations'
        ], capture_output=True, text=True, cwd=BASE_DIR)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ Failed to show migration status")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error showing migration status: {e}")

def check_database_connection():
    """Check if database connection is working."""
    print("🔌 Checking database connection...")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main function to orchestrate the migration process."""
    print("🚀 Django Migration Management Script")
    print("=" * 50)
    
    # Check database connection first
    if not check_database_connection():
        print("❌ Cannot proceed without database connection")
        return False
    
    # Get all apps
    apps_list = get_all_apps()
    print(f"📋 Found {len(apps_list)} installed apps")
    
    # Create migration folders for missing apps
    create_migration_folders()
    
    # Show initial status
    print("\n📊 Initial migration status:")
    show_migration_status()
    
    # Run makemigrations
    if not run_makemigrations():
        print("❌ Failed to create migrations")
        return False
    
    # Wait a moment for files to be written
    time.sleep(1)
    
    # Run migrate
    if not run_migrate():
        print("❌ Failed to apply migrations")
        return False
    
    # Show final status
    print("\n📊 Final migration status:")
    show_migration_status()
    
    print("\n🎉 Migration process completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 