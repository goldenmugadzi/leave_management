#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('D:/b')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.db import connection

print("Current Asset_Register migration records:")
with connection.cursor() as cursor:
    cursor.execute("SELECT id, app, name FROM django_migrations WHERE app = 'Asset_Register' ORDER BY id")
    rows = cursor.fetchall()
    
    for id, app, name in rows:
        print(f"  {id}: {app}: {name}")

print("\nRemoving Asset_Register migration records...")
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'Asset_Register'")
    print("Asset_Register migration records removed")

print("\nVerifying removal...")
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'Asset_Register' ORDER BY id")
    rows = cursor.fetchall()
    
    if rows:
        for app, name in rows:
            print(f"  {app}: {name}")
    else:
        print("  No Asset_Register migrations found - cleanup successful")

print("\nCleanup completed! You can now run migrations in the correct order.")