"""
Test access levels for different role hierarchies:
- FD/MD: System-wide access (all records)
- EM/GM: Cost center limited + region-wide fallback
- Accounting Officer/Finance Manager: Cost center limited + region-wide fallback
- Others: Cost center limited + section-only fallback
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import UserProfile
from approve.models import Roles
from ACE2.models import Ace2
from finance.PettyCash.models import Pettycash

print('=' * 80)
print('ROLE-BASED ACCESS LEVEL TEST')
print('=' * 80)

# Define access level categories
role_categories = {
    'System-Wide Access (FD/MD)': [
        'Finance Director/Transmission Manager',
        'Managing Director'
    ],
    'Region-Wide Fallback (AO/FM/EM/GM)': [
        'Accounting Officer',
        'Finance Manager',
        'Engineering Manager',
        'General Manager/Transmission Distribution Director'
    ],
    'Section-Only Fallback': [
        'Section Head / District Manager/(RTM transmisssion)',
        'Requester'
    ]
}

print('\n=== Role Categories ===')
for category, roles in role_categories.items():
    print(f'\n{category}:')
    for role in roles:
        print(f'  - {role}')

# Test Statistics
print('\n=== Database Statistics ===')
total_aces = Ace2.objects.count()
aces_with_cc = Ace2.objects.filter(cost_center__isnull=False).count()
aces_without_cc = Ace2.objects.filter(cost_center__isnull=True).count()
print(f'Total ACEs: {total_aces}')
print(f'  - With cost centers: {aces_with_cc}')
print(f'  - Without cost centers: {aces_without_cc}')

total_pc = Pettycash.objects.count()
pc_with_cc = Pettycash.objects.filter(cost_center__isnull=False).count()
pc_without_cc = Pettycash.objects.filter(cost_center__isnull=True).count()
print(f'\nTotal PettyCash: {total_pc}')
print(f'  - With cost centers: {pc_with_cc}')
print(f'  - Without cost centers: {pc_without_cc}')

# Test each role category
print('\n' + '=' * 80)
print('ACCESS LEVEL VERIFICATION')
print('=' * 80)

# Test 1: System-Wide Access
print('\n--- Test 1: Finance Director/Managing Director (System-Wide) ---')
fd_role = Roles.objects.filter(name__in=['Finance Director/Transmission Manager', 'Managing Director']).first()
if fd_role:
    fd_user = UserProfile.objects.filter(roles=fd_role).first()
    if fd_user:
        print(f'Test User: {fd_user.username} ({fd_role.name})')
        print(f'Cost Centers: {fd_user.cost_centers_for(["ace"]) if hasattr(fd_user, "cost_centers_for") else "N/A"}')
        
        user_roles = set(fd_user.roles.all())
        system_wide_roles = ['Finance Director/Transmission Manager', 'Managing Director']
        has_system_wide = any(role.name in system_wide_roles for role in user_roles)
        
        print(f'Has System-Wide Access: {has_system_wide}')
        print(f'\n✓ Should see ALL {aces_with_cc} ACEs with cost centers')
        print(f'✓ Should see ALL {aces_without_cc} ACEs without cost centers (no region filter)')
    else:
        print('No FD/MD user found in database')
else:
    print('FD/MD role not found')

# Test 2: Region-Wide Access
print('\n--- Test 2: Accounting Officer/Finance Manager/EM/GM (Region-Wide) ---')
ao_role = Roles.objects.filter(name='Accounting Officer').first()
if ao_role:
    ao_user = UserProfile.objects.filter(
        roles=ao_role,
        section__isnull=False,
        region__isnull=False
    ).first()
    
    if ao_user:
        print(f'Test User: {ao_user.username} ({ao_role.name})')
        print(f'Section: {ao_user.section}')
        print(f'Region: {ao_user.region}')
        
        cost_centers = ao_user.cost_centers_for(["ace"])
        print(f'Designated Cost Centers: {len(list(cost_centers)) if cost_centers else 0}')
        
        user_roles = set(ao_user.roles.all())
        region_wide_roles = ['Accounting Officer', 'Finance Manager', 'Engineering Manager', 
                            'General Manager/Transmission Distribution Director']
        has_region_wide = any(role.name in region_wide_roles for role in user_roles)
        
        print(f'Has Region-Wide Access: {has_region_wide}')
        
        # Check fallback visibility
        region_aces = Ace2.objects.filter(
            cost_center__isnull=True,
            region=ao_user.region,
            date_created__year__gte=2025
        ).exclude(process__approval__approved='Rejected').count()
        
        section_aces = Ace2.objects.filter(
            cost_center__isnull=True,
            region=ao_user.region,
            section=ao_user.section,
            date_created__year__gte=2025
        ).exclude(process__approval__approved='Rejected').count()
        
        print(f'\n✓ Limited to designated cost centers for records WITH cost centers')
        print(f'✓ Should see {region_aces} ACEs without cost centers (entire region)')
        print(f'  (vs {section_aces} if limited to section only)')

# Test 3: Section-Only Access
print('\n--- Test 3: Section Head (Section-Only) ---')
sh_role = Roles.objects.filter(name='Section Head / District Manager/(RTM transmisssion)').first()
if sh_role:
    sh_user = UserProfile.objects.filter(
        roles=sh_role,
        section__isnull=False,
        region__isnull=False
    ).exclude(
        roles__name__in=['Accounting Officer', 'Finance Manager', 'Engineering Manager',
                        'General Manager/Transmission Distribution Director',
                        'Finance Director/Transmission Manager', 'Managing Director']
    ).first()
    
    if sh_user:
        print(f'Test User: {sh_user.username} ({sh_role.name})')
        print(f'Section: {sh_user.section}')
        print(f'Region: {sh_user.region}')
        
        cost_centers = sh_user.cost_centers_for(["ace"])
        print(f'Designated Cost Centers: {len(list(cost_centers)) if cost_centers else 0}')
        
        # Check fallback visibility
        section_aces = Ace2.objects.filter(
            cost_center__isnull=True,
            region=sh_user.region,
            section=sh_user.section,
            date_created__year__gte=2025
        ).exclude(process__approval__approved='Rejected').count()
        
        region_aces = Ace2.objects.filter(
            cost_center__isnull=True,
            region=sh_user.region,
            date_created__year__gte=2025
        ).exclude(process__approval__approved='Rejected').count()
        
        print(f'\n✓ Limited to designated cost centers for records WITH cost centers')
        print(f'✓ Should see {section_aces} ACEs without cost centers (section only)')
        print(f'  (vs {region_aces} in entire region)')

print('\n' + '=' * 80)
print('SUMMARY: Access Hierarchy')
print('=' * 80)
print('''
1. FD/MD (System-Wide):
   ✓ Cost Centers: ALL records with cost centers
   ✓ Fallback: ALL records without cost centers (no region filter)

2. AO/FM/EM/GM (Region-Wide):
   ✓ Cost Centers: LIMITED to designated cost centers
   ✓ Fallback: ENTIRE REGION (all sections in their region)

3. Section Head/Others (Section-Only):
   ✓ Cost Centers: LIMITED to designated cost centers
   ✓ Fallback: SECTION ONLY (their section in their region)
''')
print('=' * 80)
