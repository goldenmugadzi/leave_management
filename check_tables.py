#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("SHOW TABLES LIKE 'users_%'")
tables = [row[0] for row in cursor.fetchall()]
print("Users tables found:", tables)

# Specifically check for the problematic table
cursor.execute("SHOW TABLES LIKE 'users_userqualification'")
result = cursor.fetchall()
if result:
    print("users_userqualification table EXISTS")
else:
    print("users_userqualification table does NOT exist")