#!/usr/bin/env python3
"""
Test script for the InspectionSyncService
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/var/www/beii_v1')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

# Activate virtual environment if needed
try:
    activate_this = '/var/www/env-beii/bin/activate_this.py'
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})
except FileNotFoundError:
    pass

django.setup()

from inspections.sync.service import InspectionSyncService
from inspections.sync.models import SyncOperation, UploadQueue, ConflictResolution
from inspections.models import ClientApplication, Customer, Contractor, InspectionReport
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

def test_sync_service():
    """Test the sync service functionality"""
    print("Testing InspectionSyncService...")

    # Create test user
    user, created = User.objects.get_or_create(
        username='test_sync_user',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("Created test user")

    # Create test customer
    customer, created = Customer.objects.get_or_create(
        customer_id='TEST-CUST-001',
        defaults={
            'full_name': 'Test Customer',
            'phone': '1234567890',
            'email': 'customer@test.com'
        }
    )
    if created:
        print("Created test customer")

    # Create test contractor
    contractor, created = Contractor.objects.get_or_create(
        contractor_id='TEST-CONT-001',
        defaults={
            'business_name': 'Test Contractor',
            'contact_person': 'John Doe',
            'phone': '0987654321',
            'email': 'contractor@test.com'
        }
    )
    if created:
        print("Created test contractor")

    # Create test application
    application, created = ClientApplication.objects.get_or_create(
        application_number='TEST-APP-001',
        defaults={
            'customer': customer,
            'contractor': contractor,
            'application_type': 'new_installation',
            'purpose': 'domestic',
            'status': 'submitted'
        }
    )
    if created:
        print("Created test application")

    # Test sync service
    sync_service = InspectionSyncService()

    print("\n1. Testing sync operation creation...")
    sync_op = sync_service.start_sync_operation('full', user)
    print(f"Created sync operation: {sync_op.id} - {sync_op.get_status_display()}")

    print("\n2. Testing upload queue management...")
    queue_manager = sync_service.upload_queue_manager

    # Add test item to queue
    queue_item = queue_manager.add_to_queue(
        operation_type='inspection_create',
        data={
            'service_no': 'TEST-001',
            'consumer_name': 'Test Consumer',
            'inspection_date': timezone.now().date(),
            'status': 'pending'
        },
        priority='normal',
        entity_type='inspection',
        created_by=user
    )
    print(f"Added item to upload queue: {queue_item.id}")

    print("\n3. Testing sync status summary...")
    summary = sync_service._get_sync_status_summary(user)
    print(f"Sync summary: {summary}")

    print("\n4. Testing conflict resolution...")
    conflict_resolver = sync_service.conflict_resolver

    # Create test conflict
    conflict = conflict_resolver.record_conflict(
        conflict_type='inspection_data',
        entity_type='inspection',
        entity_id=uuid.uuid4(),
        local_data={'status': 'pass', 'updated_at': timezone.now()},
        server_data={'status': 'fail', 'updated_at': timezone.now()},
        sync_operation=sync_op
    )
    print(f"Created test conflict: {conflict.id}")

    print("\n5. Testing conflict resolution...")
    if conflict_resolver._can_auto_resolve(conflict):
        conflict_resolver._auto_resolve_conflict(conflict)
        print("Auto-resolved conflict")
    else:
        print("Conflict requires manual resolution")

    print("\n6. Completing sync operation...")
    sync_service.complete_sync_operation(records_affected=1)

    print("\n✅ Sync service test completed successfully!")

    # Cleanup
    print("\nCleaning up test data...")
    try:
        sync_op.delete()
        queue_item.delete()
        conflict.delete()
        print("Test data cleaned up")
    except:
        print("Some cleanup failed (may not be critical)")

if __name__ == '__main__':
    test_sync_service()
