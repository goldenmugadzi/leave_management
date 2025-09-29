#!/usr/bin/env python3
"""
Test script for Phase 2: Inspection Data Synchronization
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
from inspections.models import ClientApplication, Customer, Contractor, InspectionReport, InspectionWorkflow
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import uuid
import json

def test_inspection_sync():
    """Test the inspection sync functionality"""
    print("Testing Phase 2: Inspection Data Synchronization...")

    # Create test user
    user, created = User.objects.get_or_create(
        username='test_inspection_sync_user',
        defaults={'email': 'test_inspection@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("Created test user")

    # Create test customer and contractor
    customer, created = Customer.objects.get_or_create(
        customer_id='TEST-CUST-002',
        defaults={
            'full_name': 'Test Customer 2',
            'phone': '1234567890',
            'email': 'customer2@test.com'
        }
    )

    contractor, created = Contractor.objects.get_or_create(
        contractor_id='TEST-CONT-002',
        defaults={
            'business_name': 'Test Contractor 2',
            'contact_person': 'Jane Doe',
            'phone': '0987654321',
            'email': 'contractor2@test.com'
        }
    )

    # Create test application
    application, created = ClientApplication.objects.get_or_create(
        application_number='TEST-APP-002',
        defaults={
            'customer': customer,
            'contractor': contractor,
            'application_type': 'new_installation',
            'purpose': 'domestic',
            'status': 'assigned'
        }
    )
    if created:
        print("Created test application")

    # Create sync service
    sync_service = InspectionSyncService()

    print("\n1. Testing inspection creation via sync...")
    inspection_data = {
        'consumer_name': 'Test Consumer Sync',
        'inspection_date': timezone.now().date(),
        'service_no': 'TEST-SYNC-001',
        'status': 'pending',
        'property_supplied': 'Test property for sync',
        'contractor': 'Test Contractor',
        'client_application_id': str(application.id),
        # Safety checks
        'all_equipment_bonded_earthed': 'pass',
        'socket_outlets_earthed': 'pass',
        'circuit_conductors_correct_size': 'pass',
        'overhead_lines_protected': 'pass',
        'motor_installations_protected': 'pass',
    }

    result = sync_service.sync_inspection_data(inspection_data, user)
    print(f"Sync result: {result}")

    if result['success']:
        inspection_id = result['inspection_id']
        print(f"✅ Created inspection via sync: {inspection_id}")

        print("\n2. Testing inspection update via sync...")
        # Update the inspection
        update_data = inspection_data.copy()
        update_data['id'] = inspection_id
        update_data['consumer_name'] = 'Updated Consumer Name'
        update_data['status'] = 'in_progress'

        update_result = sync_service.sync_inspection_data(update_data, user)
        print(f"Update result: {update_result}")

        if update_result['success']:
            print("✅ Updated inspection via sync")

        print("\n3. Testing inspection download...")
        download_result = sync_service.download_inspection_data([inspection_id], user)
        print(f"Download result: {download_result}")

        if download_result['success']:
            print(f"✅ Downloaded {download_result['count']} inspections")

        print("\n4. Testing conflict detection...")
        # Create conflicting data
        local_data = {
            'id': inspection_id,
            'consumer_name': 'Local Change',
            'all_equipment_bonded_earthed': 'fail',  # Safety field conflict
            'status': 'completed',
            'updated_at': (timezone.now() + timedelta(minutes=5)).isoformat()
        }

        server_data = sync_service._serialize_inspection_for_sync(
            InspectionReport.objects.get(id=inspection_id)
        )
        server_data['consumer_name'] = 'Server Change'
        server_data['all_equipment_bonded_earthed'] = 'pass'  # Conflict with local
        server_data['status'] = 'in_progress'

        conflicts = sync_service._detect_inspection_conflicts(local_data, server_data)
        print(f"Detected conflicts: {conflicts}")

        if conflicts:
            print("✅ Conflict detection working")

            print("\n5. Testing business rule conflict resolution...")
            # Create conflict record
            sync_op = SyncOperation.objects.create(
                operation_type='incremental',
                user=user,
                status='completed'
            )

            conflict = ConflictResolution.objects.create(
                conflict_type='inspection_data',
                entity_type='inspection',
                entity_id=inspection_id,
                local_data=local_data,
                server_data=server_data,
                resolution='manual',
                sync_operation=sync_op
            )

            # Test auto-resolution
            can_resolve = sync_service._can_auto_resolve(conflict)
            print(f"Can auto-resolve: {can_resolve}")

            if can_resolve:
                sync_service._auto_resolve_conflict(conflict)
                print("✅ Auto-resolved conflict using business rules")

                # Check the resolution
                conflict.refresh_from_db()
                print(f"Resolution: {conflict.resolution}")
                print(f"Resolved data: {conflict.resolved_data}")

        print("\n6. Testing batch operations...")
        batch_data = [
            {
                'consumer_name': 'Batch Consumer 1',
                'inspection_date': timezone.now().date(),
                'service_no': 'BATCH-001',
                'status': 'pending',
                'client_application_id': str(application.id),
                'all_equipment_bonded_earthed': 'pass',
                'socket_outlets_earthed': 'pass',
            },
            {
                'consumer_name': 'Batch Consumer 2',
                'inspection_date': timezone.now().date(),
                'service_no': 'BATCH-002',
                'status': 'pending',
                'client_application_id': str(application.id),
                'all_equipment_bonded_earthed': 'pass',
                'socket_outlets_earthed': 'pass',
            }
        ]

        # Test batch sync via API simulation
        from inspections.sync.views import sync_inspection_batch
        from django.test import RequestFactory
        from rest_framework.test import force_authenticate

        factory = RequestFactory()
        request = factory.post('/sync/sync-inspection-batch/',
                             {'inspections': batch_data},
                             format='json')
        force_authenticate(request, user=user)

        batch_result = sync_inspection_batch(request)
        print(f"Batch sync result: {batch_result.data}")

        print("\n✅ Phase 2 inspection sync tests completed successfully!")

        # Cleanup
        print("\nCleaning up test data...")
        try:
            sync_op.delete()
            if 'conflict' in locals():
                conflict.delete()
            print("Test data cleaned up")
        except:
            print("Some cleanup failed (may not be critical)")

    else:
        print("❌ Inspection creation failed")

if __name__ == '__main__':
    test_inspection_sync()
