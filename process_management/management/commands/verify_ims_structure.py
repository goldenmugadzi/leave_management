from django.core.management.base import BaseCommand
from django.db import transaction
from process_management.models import ProcessDepartment, Process
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Verify IMS data structure implementation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--run-migration',
            action='store_true',
            help='Run the IMS processes migration before verification',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information about each process',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Starting IMS Data Structure Verification...')
        )

        # Run migration if requested
        if options['run_migration']:
            self.stdout.write('📦 Running IMS processes migration...')
            try:
                call_command('migrate', 'process_management', verbosity=0)
                self.stdout.write(
                    self.style.SUCCESS('✅ Migration completed successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Migration failed: {e}')
                )
                return

        # Verify departments
        self.verify_departments()
        
        # Verify processes
        self.verify_processes(options['detailed'])
        
        # Generate summary
        self.generate_summary()

    def verify_departments(self):
        """Verify that all IMS departments exist"""
        self.stdout.write('\n📋 Verifying IMS Departments...')
        
        expected_departments = ['MANAGEMENT', 'TRANSPORT', 'DISTRICTS']
        departments = ProcessDepartment.objects.filter(name__in=expected_departments)
        
        if departments.count() == 3:
            self.stdout.write(
                self.style.SUCCESS('✅ All 3 IMS departments found')
            )
            for dept in departments:
                self.stdout.write(f'   • {dept.name} (Order: {dept.order})')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Expected 3 departments, found {departments.count()}')
            )
            missing = set(expected_departments) - set(departments.values_list('name', flat=True))
            if missing:
                self.stdout.write(
                    self.style.WARNING(f'   Missing departments: {", ".join(missing)}')
                )

    def verify_processes(self, detailed=False):
        """Verify that all IMS processes exist"""
        self.stdout.write('\n📊 Verifying IMS Processes...')
        
        # Expected process counts by department
        expected_counts = {
            'MANAGEMENT': 10,
            'TRANSPORT': 9,
            'DISTRICTS': 21,
        }
        
        total_expected = sum(expected_counts.values())
        
        # Get all processes with IMS references
        ims_processes = Process.objects.filter(ims_reference__startswith='ZETDC-HRE')
        
        if ims_processes.count() == total_expected:
            self.stdout.write(
                self.style.SUCCESS(f'✅ All {total_expected} IMS processes found')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Expected {total_expected} processes, found {ims_processes.count()}')
            )

        # Check by department
        for dept_name, expected_count in expected_counts.items():
            try:
                dept = ProcessDepartment.objects.get(name=dept_name)
                dept_processes = ims_processes.filter(department=dept)
                
                if dept_processes.count() == expected_count:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {dept_name}: {dept_processes.count()}/{expected_count}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ {dept_name}: {dept_processes.count()}/{expected_count}')
                    )
                
                if detailed:
                    for process in dept_processes:
                        self.stdout.write(f'      • {process.ims_reference}: {process.name}')
                        
            except ProcessDepartment.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Department {dept_name} not found')
                )

    def generate_summary(self):
        """Generate a summary of the IMS structure"""
        self.stdout.write('\n📈 IMS Structure Summary:')
        
        # Department summary
        departments = ProcessDepartment.objects.all()
        self.stdout.write(f'   📋 Total Departments: {departments.count()}')
        
        # Process summary
        total_processes = Process.objects.count()
        ims_processes = Process.objects.filter(ims_reference__startswith='ZETDC-HRE')
        non_ims_processes = total_processes - ims_processes.count()
        
        self.stdout.write(f'   📊 Total Processes: {total_processes}')
        self.stdout.write(f'   ✅ IMS Processes: {ims_processes.count()}')
        self.stdout.write(f'   📝 Non-IMS Processes: {non_ims_processes}')
        
        # Document types summary
        from process_management.models import ProcessDocument
        document_types = ProcessDocument.DOCUMENT_TYPES
        self.stdout.write(f'   📄 Document Types: {len(document_types)}')
        
        # Compliance status summary
        compliance_statuses = ProcessDocument.COMPLIANCE_STATUS_CHOICES
        self.stdout.write(f'   🎯 Compliance Statuses: {len(compliance_statuses)}')
        
        self.stdout.write('\n🎉 IMS Data Structure Verification Complete!')
        
        if ims_processes.count() == 40:  # Total expected IMS processes
            self.stdout.write(
                self.style.SUCCESS('✅ Phase 2 Implementation: SUCCESS')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Phase 2 Implementation: INCOMPLETE')
            )
