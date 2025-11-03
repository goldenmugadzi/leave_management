import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.db import connection

# Check for ACE2 records with invalid section_id
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) FROM ACE2_ace2 
        WHERE section_id NOT IN (SELECT id FROM users_sections)
        OR section_id IS NULL
    """)
    invalid_count = cursor.fetchone()[0]
    print(f"ACE2 records with invalid/null section_id: {invalid_count}")
    
    if invalid_count > 0:
        cursor.execute("""
            SELECT Ace_id, Ace_id2, section_id 
            FROM ACE2_ace2 
            WHERE section_id NOT IN (SELECT id FROM users_sections)
            OR section_id IS NULL
            LIMIT 10
        """)
        print("\nFirst 10 invalid records:")
        for row in cursor.fetchall():
            print(f"  ACE ID: {row[0]}, ACE_ID2: {row[1]}, Section ID: {row[2]}")
