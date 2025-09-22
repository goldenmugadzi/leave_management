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

# The migration files that actually exist in the filesystem
filesystem_migrations = [
    '0001_initial',
    '0002_alter_userprofile_email_alter_userprofile_last_reset',
    '0004_alter_userprofile_last_reset',
    '0005_alter_userprofile_last_reset',
    '0006_alter_userprofile_last_reset',
    '0007_userprofile_grade_userprofile_national_id_and_more',
    '0008_remove_userprofile_grade_and_more',
    '0009_alter_userprofile_last_reset',
    '0010_userprofile_grade_userprofile_national_id_and_more',
]

print("Current migration records in database:")
with connection.cursor() as cursor:
    cursor.execute("SELECT id, app, name FROM django_migrations WHERE app = 'users' ORDER BY id")
    rows = cursor.fetchall()
    
    for id, app, name in rows:
        print(f"  {id}: {app}: {name}")

print(f"\nMigration files in filesystem:")
for migration in filesystem_migrations:
    print(f"  users: {migration}")

print("\nCleaning up migration records...")
with connection.cursor() as cursor:
    # Delete all users migration records
    cursor.execute("DELETE FROM django_migrations WHERE app = 'users'")
    print(f"Deleted all users migration records")
    
    # Add back only the ones that should be applied based on our earlier analysis
    migrations_to_add = [
        '0001_initial',  # This was applied
        '0002_alter_userprofile_email_alter_userprofile_last_reset',  # We'll add this
        '0004_alter_userprofile_last_reset',  # This was applied
        '0005_alter_userprofile_last_reset',  # This was applied
        '0006_alter_userprofile_last_reset',  # This was applied
        # '0007' through '0010' were not applied, so we won't add them
    ]
    
    for migration in migrations_to_add:
        cursor.execute(
            "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
            ['users', migration, '2025-09-22 14:15:00']
        )
        print(f"Added: users.{migration}")

print("\nUpdated migration records:")
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'users' ORDER BY id")
    rows = cursor.fetchall()
    
    for app, name in rows:
        print(f"  {app}: {name}")

print("\nMigration history cleanup completed!")