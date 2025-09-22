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

print("Asset_Register migration records in database:")
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'Asset_Register' ORDER BY id")
    rows = cursor.fetchall()
    
    for app, name in rows:
        print(f"  {app}: {name}")

if not rows:
    print("  No Asset_Register migrations found in database")