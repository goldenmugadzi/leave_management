"""
Fix Golowa's region to match the PettyCash items in section 27

Option 1: Update Golowa's region to 141 (to match PC20251013800)
Option 2: Update all Section 27 PettyCash items to region 1 (to match Golowa)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Check how many PettyCash items are in each region for section 27
print("=== PettyCash distribution for Section 27 ===")
cursor.execute('''
    SELECT r.region, r.id, COUNT(*) as count
    FROM PettyCash_pettycash pc
    JOIN users_regions r ON pc.region_id = r.id
    WHERE pc.section_id = 27
    GROUP BY r.id
    ORDER BY count DESC
''')
results = cursor.fetchall()
for row in results:
    print(f"Region: {row[0]} (ID: {row[1]}) - {row[2]} PettyCash items")

print("\n=== Recommendation ===")
most_common_region_id = results[0][1] if results else None
if most_common_region_id:
    print(f"Most PettyCash items in section 27 are in Region ID: {most_common_region_id}")
    print(f"\nOption 1: Update Golowa's region from ID 1 to ID {most_common_region_id}")
    print(f"SQL: UPDATE users_userprofile SET region_id = {most_common_region_id} WHERE id = 206;")
    
    print(f"\nOption 2: Update all Section 27 PettyCash items to Region ID 1 (Golowa's region)")
    print(f"SQL: UPDATE PettyCash_pettycash SET region_id = 1 WHERE section_id = 27 AND region_id != 1;")
    
    print("\n⚠️  WARNING: Before running either SQL, backup your database!")
    print("You can run this in Django shell or MySQL directly.")

# Check if there are users in section 27 with different regions
print("\n=== Users in Section 27 with different regions ===")
cursor.execute('''
    SELECT DISTINCT r.region, r.id, COUNT(*) as user_count
    FROM users_userprofile up
    JOIN users_regions r ON up.region_id = r.id
    WHERE up.section_id = 27
    GROUP BY r.id
    ORDER BY user_count DESC
''')
user_regions = cursor.fetchall()
for row in user_regions:
    print(f"Region: {row[0]} (ID: {row[1]}) - {row[2]} users")

cursor.close()
