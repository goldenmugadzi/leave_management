#!/usr/bin/env python
"""
Test script for equipment management functionality
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from equipment_management.models import Equipment, EquipmentOperation, EquipmentHistory
from django.contrib.auth import get_user_model

User = get_user_model()
from datetime import date

def test_equipment_management():
    print("Testing Equipment Management System...")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Created test user: {user}")
    else:
        print(f"Using existing user: {user}")
    
    # Test creating equipment
    try:
        equipment = Equipment.objects.create(
            equipment_type='transformer',
            make='ABB',
            serial_number=f'TEST-{date.today().strftime("%Y%m%d")}-001',
            voltage_rating='33kV',
            kva_rating=1000,
            ampere_rating=50,
            location_description='Test substation - Section A',
            substation_name='Test Substation',
            section='Section A',
            district='Test District',
            installation_date=date.today(),
            status='active',
            created_by=user
        )
        print(f"✓ Created equipment: {equipment}")
        
        # Test creating history
        history = EquipmentHistory.objects.create(
            equipment=equipment,
            action_type='created',
            action_description=f'Equipment created by test script',
            performed_by=user
        )
        print(f"✓ Created equipment history: {history}")
        
        # Test creating operation
        operation = EquipmentOperation.objects.create(
            operation_type='installation',
            consumer_name='Test Consumer',
            substation_name='Test Substation',
            section='Section A',
            district='Test District',
            equipment_installed=equipment,
            reason='Initial installation test',
            operator_name='Test Operator',
            operator_designation='Technician',
            operation_date=date.today(),
            priority='medium',
            created_by=user
        )
        print(f"✓ Created operation: {operation}")
        
        print("\n--- Summary ---")
        print(f"Total Equipment: {Equipment.objects.count()}")
        print(f"Total Operations: {EquipmentOperation.objects.count()}")
        print(f"Total History Records: {EquipmentHistory.objects.count()}")
        
        print("\n--- Equipment List ---")
        for eq in Equipment.objects.all():
            print(f"- {eq.serial_number}: {eq.get_equipment_type_display()} ({eq.get_status_display()})")
            
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_equipment_urls():
    """Test if equipment management URLs are accessible"""
    from django.test import Client
    from django.urls import reverse
    
    client = Client()
    
    try:
        # Test dashboard
        response = client.get('/equipment/')
        print(f"Dashboard URL (/equipment/): Status {response.status_code}")
        
        # Test equipment list
        response = client.get('/equipment/equipment/')
        print(f"Equipment List URL (/equipment/equipment/): Status {response.status_code}")
        
        # Test equipment create
        response = client.get('/equipment/equipment/create/')
        print(f"Equipment Create URL (/equipment/equipment/create/): Status {response.status_code}")
        
        return True
    except Exception as e:
        print(f"✗ URL Test Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("EQUIPMENT MANAGEMENT TEST SCRIPT")
    print("=" * 50)
    
    # Test database operations
    success1 = test_equipment_management()
    
    print("\n" + "=" * 50)
    print("TESTING URLS")
    print("=" * 50)
    
    # Test URLs
    success2 = test_equipment_urls()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 50)
