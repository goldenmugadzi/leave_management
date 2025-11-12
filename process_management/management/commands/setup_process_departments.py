"""
Django management command for setting up process departments.

This command creates the standard process departments that will be used
during the Knowledge Center migration.

Usage:
    python manage.py setup_process_departments [options]

Examples:
    # Create standard departments
    python manage.py setup_process_departments
    
    # Create departments from custom JSON file
    python manage.py setup_process_departments --from-file=departments.json
    
    # Update existing departments
    python manage.py setup_process_departments --update
"""

import json
from django.core.management.base import BaseCommand
from django.db import transaction

from process_management.models import ProcessDepartment


class Command(BaseCommand):
    help = 'Set up process departments for migration'
    
    # Standard departments based on your organizational structure
    STANDARD_DEPARTMENTS = [
        {
            'name': 'Commercial',
            'description': 'Commercial operations, customer relations, and revenue management',
            'order': 1,
        },
        {
            'name': 'Engineering',
            'description': 'Engineering processes, technical operations, and infrastructure support',
            'order': 2,
        },
        {
            'name': 'Management Processes',
            'description': 'Executive leadership, governance, and strategic coordination',
            'order': 3,
        },
        {
            'name': 'Information Communication Technology',
            'description': 'ICT strategy, systems, and technology service delivery',
            'order': 4,
        },
        {
            'name': 'Finance',
            'description': 'Financial management, budgeting, and accounting controls',
            'order': 5,
        },
        {
            'name': 'Human Resources',
            'description': 'People management, talent development, and organizational support',
            'order': 6,
        },
        {
            'name': 'Risk Management',
            'description': 'Enterprise risk governance, assessment, and mitigation',
            'order': 7,
        },
        {
            'name': 'Procurement',
            'description': 'Supply chain management, sourcing, and vendor coordination',
            'order': 8,
        },
        {
            'name': 'Stakeholder Relations',
            'description': 'Corporate communications, stakeholder engagement, and partnerships',
            'order': 9,
        },
        {
            'name': 'Legal Services',
            'description': 'Legal advisory, compliance, and contractual management',
            'order': 10,
        },
        {
            'name': 'Operations and Maintenance',
            'description': 'Network operations, maintenance planning, and asset reliability',
            'order': 11,
        },
        {
            'name': 'Transport',
            'description': 'Fleet operations, logistics coordination, and mobility support',
            'order': 12,
        },
        {
            'name': 'Network Development',
            'description': 'Grid expansion, capital projects, and development planning',
            'order': 13,
        },
        {
            'name': 'Districts',
            'description': 'District-level operations, service delivery, and regional oversight',
            'order': 14,
        },
    ]
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        
        parser.add_argument(
            '--from-file',
            type=str,
            help='Load departments from JSON file instead of using standard list'
        )
        
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing departments instead of skipping them'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )
        
        parser.add_argument(
            '--export-template',
            type=str,
            help='Export department template to JSON file'
        )
    
    def handle(self, *args, **options):
        """Execute the setup command."""
        
        try:
            # Export template if requested
            if options.get('export_template'):
                self._export_template(options['export_template'])
                return
            
            # Load departments
            if options.get('from_file'):
                departments = self._load_departments_from_file(options['from_file'])
            else:
                departments = self.STANDARD_DEPARTMENTS
            
            # Validate departments
            self._validate_departments(departments)
            
            # Create/update departments
            if options['dry_run']:
                self._dry_run_setup(departments, options['update'])
            else:
                self._setup_departments(departments, options['update'])
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Setup failed: {str(e)}')
            )
            raise
    
    def _load_departments_from_file(self, filename):
        """Load departments from JSON file."""
        
        try:
            with open(filename, 'r') as f:
                departments = json.load(f)
            
            self.stdout.write(f"Loaded {len(departments)} departments from {filename}")
            return departments
            
        except FileNotFoundError:
            raise Exception(f"File not found: {filename}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in {filename}: {e}")
    
    def _validate_departments(self, departments):
        """Validate department data."""
        
        if not isinstance(departments, list):
            raise Exception("Departments must be a list")
        
        required_fields = ['name', 'description', 'order']
        names = set()
        orders = set()
        
        for i, dept in enumerate(departments):
            if not isinstance(dept, dict):
                raise Exception(f"Department {i} must be a dictionary")
            
            # Check required fields
            for field in required_fields:
                if field not in dept:
                    raise Exception(f"Department {i} missing required field: {field}")
            
            # Check for duplicates
            name = dept['name']
            order = dept['order']
            
            if name in names:
                raise Exception(f"Duplicate department name: {name}")
            if order in orders:
                raise Exception(f"Duplicate department order: {order}")
            
            names.add(name)
            orders.add(order)
            
            # Validate field types
            if not isinstance(name, str) or len(name.strip()) == 0:
                raise Exception(f"Department {i} name must be a non-empty string")
            
            if not isinstance(dept['description'], str):
                raise Exception(f"Department {i} description must be a string")
            
            if not isinstance(order, int) or order < 0:
                raise Exception(f"Department {i} order must be a non-negative integer")
        
        self.stdout.write(f"Validated {len(departments)} departments")
    
    def _dry_run_setup(self, departments, update_existing):
        """Perform dry run of department setup."""
        
        self.stdout.write("DRY RUN - No changes will be made")
        self.stdout.write("=" * 40)
        
        stats = {
            'to_create': 0,
            'to_update': 0,
            'to_skip': 0
        }
        
        for dept in departments:
            existing = ProcessDepartment.objects.filter(name=dept['name']).first()
            
            if existing:
                if update_existing:
                    stats['to_update'] += 1
                    self.stdout.write(f"Would UPDATE: {dept['name']}")
                    if existing.description != dept['description']:
                        self.stdout.write(f"  Description: '{existing.description}' -> '{dept['description']}'")
                    if existing.order != dept['order']:
                        self.stdout.write(f"  Order: {existing.order} -> {dept['order']}")
                else:
                    stats['to_skip'] += 1
                    self.stdout.write(f"Would SKIP: {dept['name']} (already exists)")
            else:
                stats['to_create'] += 1
                self.stdout.write(f"Would CREATE: {dept['name']}")
        
        self.stdout.write("\nDry Run Summary:")
        self.stdout.write(f"  To create: {stats['to_create']}")
        self.stdout.write(f"  To update: {stats['to_update']}")
        self.stdout.write(f"  To skip: {stats['to_skip']}")
    
    def _setup_departments(self, departments, update_existing):
        """Create or update departments."""
        
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        with transaction.atomic():
            for dept in departments:
                try:
                    existing = ProcessDepartment.objects.filter(name=dept['name']).first()
                    
                    if existing:
                        if update_existing:
                            # Update existing department
                            updated = False
                            
                            if existing.description != dept['description']:
                                existing.description = dept['description']
                                updated = True
                            
                            if existing.order != dept['order']:
                                existing.order = dept['order']
                                updated = True
                            
                            if updated:
                                existing.save()
                                stats['updated'] += 1
                                self.stdout.write(f"Updated: {dept['name']}")
                            else:
                                stats['skipped'] += 1
                                self.stdout.write(f"No changes needed: {dept['name']}")
                        else:
                            stats['skipped'] += 1
                            self.stdout.write(f"Skipped (exists): {dept['name']}")
                    else:
                        # Create new department
                        ProcessDepartment.objects.create(
                            name=dept['name'],
                            description=dept['description'],
                            order=dept['order']
                        )
                        stats['created'] += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"Created: {dept['name']}")
                        )
                
                except Exception as e:
                    stats['errors'] += 1
                    self.stdout.write(
                        self.style.ERROR(f"Error with {dept['name']}: {e}")
                    )
        
        # Display summary
        self.stdout.write("\nSetup Summary:")
        self.stdout.write(f"  Created: {stats['created']}")
        self.stdout.write(f"  Updated: {stats['updated']}")
        self.stdout.write(f"  Skipped: {stats['skipped']}")
        
        if stats['errors'] > 0:
            self.stdout.write(
                self.style.WARNING(f"  Errors: {stats['errors']}")
            )
        
        if stats['created'] > 0 or stats['updated'] > 0:
            self.stdout.write(
                self.style.SUCCESS("Department setup completed successfully!")
            )
    
    def _export_template(self, filename):
        """Export department template to JSON file."""
        
        try:
            template = {
                "departments": self.STANDARD_DEPARTMENTS,
                "instructions": {
                    "description": "Template for process departments",
                    "fields": {
                        "name": "Department name (must be unique)",
                        "description": "Department description",
                        "order": "Display order (integer, must be unique)"
                    },
                    "usage": "python manage.py setup_process_departments --from-file=departments.json"
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(template, f, indent=2)
            
            self.stdout.write(f"Template exported to: {filename}")
            self.stdout.write("Edit the file and use --from-file to load custom departments")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Could not export template: {e}")
            )