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

print("Checking users_userprofile table structure...")
with connection.cursor() as cursor:
    cursor.execute("DESCRIBE users_userprofile")
    columns = cursor.fetchall()
    
    print("Existing columns:")
    for column in columns:
        print(f"  {column[0]} - {column[1]}")
    
    # Check specifically for grade and national_id columns
    column_names = [col[0] for col in columns]
    print(f"\nColumns of interest:")
    print(f"  'grade' exists: {'grade' in column_names}")
    print(f"  'national_id' exists: {'national_id' in column_names}")