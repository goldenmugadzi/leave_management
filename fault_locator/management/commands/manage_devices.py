from django.core.management.base import BaseCommand
from fault_locator.models import FaultLocatorDevice, FaultLocatorDeviceAssignment, FaultLocatorTeam

class Command(BaseCommand):
    help = 'Manage fault locator devices - create, list, or unassign'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            choices=['list', 'create', 'unassign-all', 'create-sample'],
            required=True,
            help='Action to perform'
        )
        parser.add_argument(
            '--serial',
            type=str,
            help='Serial number for device creation'
        )
        parser.add_argument(
            '--description',
            type=str,
            help='Description for device creation'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            self.list_devices()
        elif action == 'create':
            self.create_device(options['serial'], options['description'])
        elif action == 'unassign-all':
            self.unassign_all_devices()
        elif action == 'create-sample':
            self.create_sample_devices()

    def list_devices(self):
        """List all devices and their assignment status"""
        self.stdout.write(self.style.SUCCESS('=== Fault Locator Devices ==='))
        
        total_devices = FaultLocatorDevice.objects.count()
        assigned_devices = FaultLocatorDeviceAssignment.objects.values_list('device_id', flat=True)
        available_count = FaultLocatorDevice.objects.exclude(id__in=assigned_devices).count()
        
        self.stdout.write(f"Total devices: {total_devices}")
        self.stdout.write(f"Available devices: {available_count}")
        self.stdout.write(f"Assigned devices: {len(assigned_devices)}")
        self.stdout.write("")
        
        # List all devices
        for device in FaultLocatorDevice.objects.all():
            assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
            if assignment:
                status = f"ASSIGNED to {assignment.team.name}"
                style = self.style.WARNING
            else:
                status = "AVAILABLE"
                style = self.style.SUCCESS
            
            self.stdout.write(
                f"{device.serial_number:15} | {device.status:12} | {status:20} | {device.description}"
            )

    def create_device(self, serial, description):
        """Create a new device"""
        if not serial:
            self.stdout.write(self.style.ERROR('Serial number is required'))
            return
        
        if not description:
            description = f"Device {serial}"
        
        try:
            device = FaultLocatorDevice.objects.create(
                serial_number=serial,
                description=description,
                status='available'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created device: {device.serial_number}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating device: {str(e)}')
            )

    def unassign_all_devices(self):
        """Unassign all devices from teams"""
        assignments = FaultLocatorDeviceAssignment.objects.all()
        count = assignments.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No devices are currently assigned'))
            return
        
        assignments.delete()
        self.stdout.write(
            self.style.SUCCESS(f'Unassigned {count} devices from teams')
        )

    def create_sample_devices(self):
        """Create sample devices for testing"""
        sample_devices = [
            {"serial": "FLD-001", "desc": "Primary Fault Locator Device"},
            {"serial": "FLD-002", "desc": "Secondary Fault Locator Device"},
            {"serial": "FLD-003", "desc": "Backup Fault Locator Device"},
            {"serial": "FLD-004", "desc": "Mobile Fault Locator Device"},
            {"serial": "FLD-005", "desc": "Emergency Fault Locator Device"},
        ]
        
        created = 0
        for device_data in sample_devices:
            device, created_new = FaultLocatorDevice.objects.get_or_create(
                serial_number=device_data["serial"],
                defaults={
                    "description": device_data["desc"],
                    "status": "available"
                }
            )
            if created_new:
                self.stdout.write(
                    self.style.SUCCESS(f'Created device: {device.serial_number}')
                )
                created += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'Device already exists: {device.serial_number}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created} new devices')
        )
