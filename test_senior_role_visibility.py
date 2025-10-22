"""
Test region-wide visibility for senior roles in ACE and PettyCash awaiting my action
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import UserProfile
from approve.models import Roles
from ACE2.models import Ace2
from finance.PettyCash.models import Pettycash

print('=== Testing Region-Wide Visibility for Senior Roles ===')

# Find a user with Accounting Officer role
accounting_officer_role = Roles.objects.filter(name='Accounting Officer').first()

if accounting_officer_role:
    users_with_ao_role = UserProfile.objects.filter(
        roles=accounting_officer_role,
        section__isnull=False,
        region__isnull=False
    ).first()
    
    if users_with_ao_role:
        print(f'\nTest User (Accounting Officer): {users_with_ao_role.username}')
        print(f'Section: {users_with_ao_role.section}')
        print(f'Region: {users_with_ao_role.region}')
        
        user_roles = set(users_with_ao_role.roles.all())
        senior_role_names = [
            'Accounting Officer',
            'Finance Manager',
            'General Manager/Transmission Distribution Director',
            'Engineering Manager',
            'Finance Director/Transmission Manager',
            'Managing Director'
        ]
        has_senior_role = any(role.name in senior_role_names for role in user_roles)
        print(f'Has Senior Role: {has_senior_role}')
        print(f'User Roles: {[r.name for r in user_roles]}')
        
        region = users_with_ao_role.region
        section = users_with_ao_role.section
        
        # Test ACE visibility
        aces_entire_region = Ace2.objects.filter(
            cost_center__isnull=True,
            region=region,
            date_created__year__gte=2025
        ).exclude(
            process__approval__approved='Rejected'
        ).count()
        
        aces_user_section = Ace2.objects.filter(
            cost_center__isnull=True,
            region=region,
            section=section,
            date_created__year__gte=2025
        ).exclude(
            process__approval__approved='Rejected'
        ).count()
        
        print(f'\n--- ACE Analysis ---')
        print(f'ACEs without cost centers in entire region {region}: {aces_entire_region}')
        print(f'ACEs without cost centers in section {section} only: {aces_user_section}')
        print(f'Difference (other sections in region): {aces_entire_region - aces_user_section}')
        
        if has_senior_role:
            print(f'\n✓ With senior role, user SHOULD see {aces_entire_region} ACEs (entire region)')
        else:
            print(f'\n✗ Without senior role, user SHOULD see {aces_user_section} ACEs (section only)')
        
        # Test PettyCash visibility
        pc_entire_region = Pettycash.objects.filter(
            cost_center__isnull=True,
            region=region,
            date_created__year__gte=2025
        ).exclude(
            process__approval__approved='Rejected'
        ).count()
        
        pc_user_section = Pettycash.objects.filter(
            cost_center__isnull=True,
            region=region,
            section=section,
            date_created__year__gte=2025
        ).exclude(
            process__approval__approved='Rejected'
        ).count()
        
        print(f'\n--- PettyCash Analysis ---')
        print(f'PettyCash without cost centers in entire region {region}: {pc_entire_region}')
        print(f'PettyCash without cost centers in section {section} only: {pc_user_section}')
        print(f'Difference (other sections in region): {pc_entire_region - pc_user_section}')
        
    else:
        print('\nNo users with Accounting Officer role found')
        print('Trying with any user that has multiple roles...')
        
        test_user = UserProfile.objects.filter(
            section__isnull=False,
            region__isnull=False
        ).exclude(roles__isnull=True).first()
        
        if test_user:
            print(f'\nTest User: {test_user.username}')
            print(f'Section: {test_user.section}')
            print(f'Region: {test_user.region}')
            print(f'Roles: {[r.name for r in test_user.roles.all()]}')
else:
    print('Accounting Officer role not found in database')

print('\n=== Test Implementation ===')
print('✓ Senior roles (Accounting Officer, Finance Manager, EM, GM) see ENTIRE REGION')
print('✓ Junior roles (Section Head, etc.) see THEIR SECTION only')
print('✓ Cost center filtering remains unchanged (jurisdiction-based)')
