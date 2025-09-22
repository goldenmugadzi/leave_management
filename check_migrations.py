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

# Query the migration table directly
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'users' ORDER BY id")
    rows = cursor.fetchall()
    
print("Current users migrations in database:")
for app, name in rows:
    print(f"  {app}: {name}")