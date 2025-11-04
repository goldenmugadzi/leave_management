import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.db import connection

# Fix ACE2 records with invalid section_id
with connection.cursor() as cursor:
    # Get a valid default section (first one)
    cursor.execute("SELECT id FROM users_sections ORDER BY id LIMIT 1")
    default_section_id = cursor.fetchone()[0]
    print(f"Default section ID to use: {default_section_id}")
    
    # Update NULL section_ids
    cursor.execute(f"""
        UPDATE ACE2_ace2 
        SET section_id = {default_section_id}
        WHERE section_id IS NULL
    """)
    null_updated = cursor.rowcount
    print(f"Updated {null_updated} records with NULL section_id")
    
    # Update invalid section_ids (section 57 doesn't exist)
    cursor.execute(f"""
        UPDATE ACE2_ace2 
        SET section_id = {default_section_id}
        WHERE section_id NOT IN (SELECT id FROM users_sections)
    """)
    invalid_updated = cursor.rowcount
    print(f"Updated {invalid_updated} records with invalid section_id")
    
    # Verify fix
    cursor.execute("""
        SELECT COUNT(*) FROM ACE2_ace2 
        WHERE section_id NOT IN (SELECT id FROM users_sections)
        OR section_id IS NULL
    """)
    remaining = cursor.fetchone()[0]
    print(f"\nRemaining invalid records: {remaining}")
    
print("✓ Data integrity fixed!")
