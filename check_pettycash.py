import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Check PC20251013800
cursor.execute('SELECT petty_id, section_id, region_id, requested_by_id FROM PettyCash_pettycash WHERE petty_id=%s', ['PC20251013800'])
row = cursor.fetchone()

if row:
    print(f'PettyCash ID: {row[0]}')
    print(f'Section ID: {row[1]}')
    print(f'Region ID: {row[2]}')
    print(f'Requested By ID: {row[3]}')
    
    # Get section name
    if row[1]:
        cursor.execute('SELECT section, code FROM users_sections WHERE id=%s', [row[1]])
        section = cursor.fetchone()
        if section:
            print(f'Section: {section[0]} ({section[1]})')
    
    # Get region name
    if row[2]:
        cursor.execute('SELECT region, code FROM users_regions WHERE id=%s', [row[2]])
        region = cursor.fetchone()
        if region:
            print(f'Region: {region[0]} ({region[1]})')
else:
    print('PettyCash PC20251013800 not found')
    
print('\n--- Golowa Details ---')
# Check Golowa's profile - correct username is ze243973
cursor.execute('SELECT id, username, section_id, region_id, designation_id FROM users_userprofile WHERE username=%s', ['ze243973'])
user = cursor.fetchone()

if user:
    print(f'\nGolowa (ze243973) Details:')
    print(f'ID: {user[0]}')
    print(f'Username: {user[1]}')
    print(f'Section ID: {user[2]}')
    print(f'Region ID: {user[3]}')
    print(f'Designation ID: {user[4]}')
    
    # Check if sections match
    if user[2] == 27:
        print('✓ SECTION MATCHES! (Both are Section 27 - Harare Region Stores)')
    else:
        print(f'✗ Section does not match (Golowa: {user[2]}, PettyCash: 27)')
    
    # Check if regions match  
    if user[3] == 141:
        print('✓ REGION MATCHES! (Both are Region 141 - Harare)')
    else:
        print(f'✗ Region does not match (Golowa: {user[3]}, PettyCash: 141)')
    
    # Get section name
    if user[2]:
        cursor.execute('SELECT section, code FROM users_sections WHERE id=%s', [user[2]])
        section = cursor.fetchone()
        if section:
            print(f'Section: {section[0]} ({section[1]})')
    
    # Get region name
    if user[3]:
        cursor.execute('SELECT region, code FROM users_regions WHERE id=%s', [user[3]])
        region = cursor.fetchone()
        if region:
            print(f'Region: {region[0]} ({region[1]})')
    
    # Get designation
    if user[4]:
        cursor.execute('SELECT description FROM users_designations WHERE id=%s', [user[4]])
        designation = cursor.fetchone()
        if designation:
            print(f'Designation: {designation[0]}')
    
    # Check roles
    cursor.execute('''
        SELECT r.application, r.role 
        FROM users_userprofile_roles upr
        JOIN users_roles r ON upr.roles_id = r.id
        WHERE upr.userprofile_id = %s
    ''', [user[0]])
    roles = cursor.fetchall()
    print(f'\nRoles:')
    if roles:
        for role in roles:
            print(f'  - {role[0]}: {role[1]}')
            if role[0] == 'pettycash':
                print(f'    → PettyCash Role: {role[1]}')
                if role[1] == 'approve':
                    print('    → ✓ Has "approve" role - should see section PettyCash items')
                else:
                    print(f'    → ✗ Role is "{role[1]}", not "approve" - may not see all section items')
    else:
        print('  → ✗ NO ROLES ASSIGNED - This is the problem!')
else:
    print('User ze243973 not found')

users = []

user = None

if not users:
    # Try checking users in section 27 (Harare Region Stores)
    print('\n--- All users in Section 27 (Harare Region Stores) ---')
    cursor.execute('''
        SELECT id, username, first_name, last_name, section_id, region_id 
        FROM users_userprofile 
        WHERE section_id = 27
        ORDER BY username
    ''')
    section_users = cursor.fetchall()
    for su in section_users:
        print(f'{su[1]} ({su[2]} {su[3]})')

cursor.close()
