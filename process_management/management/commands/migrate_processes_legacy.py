"""
Django management command to migrate existing folder-based processes to the new relational structure.
"""
import os
import json
import traceback
from typing import Dict, List, Optional, Tuple
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.conf import settings
from django.utils import timezone

from process_management.models import ProcessDepartment, Process, ProcessDocument
from process_management.services import FolderAnalysisService, DocumentCategorizationService
from knowledge_center.models import (
    FolderApplication, KnowledgeCentreFolder, KnowldgeCentreFile, 
    KnowledgeCenter
)
from it.users.models import Regions, Sections, UserProfile


class Command(BaseCommand):
    help = 'Migrate existing folder-based processes to the new relational structure'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder_service = FolderAnalysisService()
        self.doc_service = DocumentCategorizationService()
        self.migration_report = {
            'start_time': None,
            'end_time': None,
            'total_processes_created': 0,
            'total_documents_migrated': 0,
            'departments_created': 0,
            'errors': [],
            'warnings': [],
            'skipped_items': [],
            'department_distribution': {},
            'rollback_info': None,
            'validation_results': {},
        }
        self.created_objects = {
            'departments': [],
            'processes': [],
            'documents': [],
        }
        self.progress_callback = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run migration in dry-run mode without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if processes already exist',
        )
        parser.add_argument(
            '--report-only',
            action='store_true',
            help='Only generate analysis report without migrating',
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file for migration report (JSON format)',
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate migration without executing',
        )
        parser.add_argument(
            '--rollback',
            action='store_true',
            help='Rollback the last migration',
        )
        parser.add_argument(
            '--progress',
            action='store_true',
            help='Show detailed progress information',
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.migration_report['start_time'] = timezone.now()
        
        # Set up progress tracking
        if options['progress']:
            self.progress_callback = self._show_progress
        
        try:
            # Handle rollback request
            if options['rollback']:
                return self._handle_rollback()
            
            self.stdout.write(
                self.style.SUCCESS('Starting process migration...')
            )
            
            # Step 1: Validate migration prerequisites
            self.stdout.write('Step 1: Validating migration prerequisites...')
            validation_result = self._validate_migration()
            
            if not validation_result['valid']:
                self.stdout.write(
                    self.style.ERROR('Migration validation failed:')
                )
                for error in validation_result['errors']:
                    self.stdout.write(f'  - {error}')
                if not options['force']:
                    return
            
            if options['validate_only']:
                self._display_validation_results(validation_result)
                return
            
            # Step 2: Analyze existing data
            self.stdout.write('Step 2: Analyzing existing processes...')
            analysis_result = self.folder_service.analyze_existing_processes()
            
            self.stdout.write(
                f'Found {analysis_result["total_processes"]} processes to migrate'
            )
            
            if options['report_only']:
                self._generate_analysis_report(analysis_result)
                return
            
            # Step 3: Execute migration with transaction and rollback support
            if options['dry_run']:
                self._execute_dry_run_migration(analysis_result)
            else:
                self._execute_migration_with_rollback(analysis_result)
            
            # Step 4: Generate final report
            self.migration_report['end_time'] = timezone.now()
            self._generate_migration_report(options.get('output_file'))
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS('Dry run completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Migration completed successfully!')
                )
                
        except Exception as e:
            self.migration_report['errors'].append(f'Fatal error: {str(e)}')
            self.migration_report['errors'].append(f'Traceback: {traceback.format_exc()}')
            self.stdout.write(
                self.style.ERROR(f'Migration failed: {str(e)}')
            )
            
            # Attempt rollback if not in dry-run mode
            if not options.get('dry_run', False):
                self.stdout.write('Attempting automatic rollback...')
                try:
                    self._rollback_migration()
                    self.stdout.write(self.style.SUCCESS('Rollback completed successfully'))
                except Exception as rollback_error:
                    self.stdout.write(
                        self.style.ERROR(f'Rollback failed: {str(rollback_error)}')
                    )
            
            raise CommandError(f'Migration failed: {str(e)}')

    def _create_departments(self, dry_run: bool = False):
        """Create predefined process departments."""
        departments = [
            ("GENERAL MANAGER'S OFFICE", "General Manager's Office", 1),
            ("ENGINEERING MANAGER'S OFFICE", "Engineering Manager's Office", 2),
            ("DISTRICTS", "Districts", 3),
            ("NETWORK DEVELOPMENT", "Network Development", 4),
            ("OPERATIONS AND MAINTENANCE", "Operations and Maintenance", 5),
            ("COMMERCIAL", "Commercial", 6),
            ("FINANCE", "Finance", 7),
            ("PROCUREMENT", "Procurement", 8),
            ("RISK MANAGEMENT", "Risk Management", 9),
            ("HUMAN RESOURCES AND ADMINISTRATION", "Human Resources and Administration", 10),
            ("INFORMATION AND COMMUNICATION TECHNOLOGY", "Information and Communication Technology", 11),
        ]
        
        created_count = 0
        
        for name, description, order in departments:
            if not dry_run:
                dept, created = ProcessDepartment.objects.get_or_create(
                    name=name,
                    defaults={
                        'description': description,
                        'order': order
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'  Created department: {name}')
                else:
                    self.stdout.write(f'  Department already exists: {name}')
            else:
                self.stdout.write(f'  [DRY RUN] Would create department: {name}')
                created_count += 1
        
        self.migration_report['departments_created'] = created_count

    def _migrate_processes(self, analysis_result: Dict, dry_run: bool = False):
        """Migrate processes from analysis results."""
        processes_created = 0
        documents_migrated = 0
        
        for dept_name, processes in analysis_result['processes_by_department'].items():
            if not dry_run:
                try:
                    department = ProcessDepartment.objects.get(name=dept_name)
                except ProcessDepartment.DoesNotExist:
                    self.migration_report['errors'].append(
                        f'Department not found: {dept_name}'
                    )
                    continue
            
            self.stdout.write(f'  Migrating {len(processes)} processes for {dept_name}')
            
            for process_data in processes:
                try:
                    process_name = self._extract_process_name(process_data['filename'])
                    
                    if not dry_run:
                        # Create process
                        process = self._create_process(
                            process_name, 
                            process_data, 
                            department
                        )
                        processes_created += 1
                        
                        # Migrate associated documents
                        docs_count = self._migrate_process_documents(
                            process, 
                            process_data
                        )
                        documents_migrated += docs_count
                        
                        self.stdout.write(f'    Created process: {process_name}')
                    else:
                        self.stdout.write(f'    [DRY RUN] Would create process: {process_name}')
                        processes_created += 1
                        documents_migrated += 1  # Estimate
                        
                except Exception as e:
                    error_msg = f'Error migrating process {process_data.get("filename", "unknown")}: {str(e)}'
                    self.migration_report['errors'].append(error_msg)
                    self.stdout.write(self.style.ERROR(f'    {error_msg}'))
        
        # Handle unmapped processes
        if analysis_result['unmapped_processes']:
            self.stdout.write(
                self.style.WARNING(
                    f'  Found {len(analysis_result["unmapped_processes"])} unmapped processes'
                )
            )
            for unmapped in analysis_result['unmapped_processes']:
                self.migration_report['skipped_items'].append({
                    'filename': unmapped.get('filename', 'unknown'),
                    'reason': 'Could not map to department',
                    'data': unmapped
                })
        
        self.migration_report['total_processes_created'] = processes_created
        self.migration_report['total_documents_migrated'] = documents_migrated
        self.migration_report['department_distribution'] = {
            dept: len(procs) for dept, procs in analysis_result['processes_by_department'].items()
        }

    def _extract_process_name(self, filename: str) -> str:
        """Extract a clean process name from filename."""
        if not filename:
            return 'Unnamed Process'
        
        # Remove file extension
        name = os.path.splitext(filename)[0]
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['process_', 'proc_', 'procedure_']
        suffixes_to_remove = ['_map', '_procedure', '_manual']
        
        name_lower = name.lower()
        for prefix in prefixes_to_remove:
            if name_lower.startswith(prefix):
                name = name[len(prefix):]
                break
        
        for suffix in suffixes_to_remove:
            if name_lower.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        # Clean up and capitalize
        name = name.replace('_', ' ').replace('-', ' ').strip()
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name or 'Unnamed Process'

    @transaction.atomic
    def _create_process(self, name: str, process_data: Dict, department: ProcessDepartment) -> Process:
        """Create a new process from migrated data."""
        # Try to get region and section
        region = None
        section = None
        
        if process_data.get('region'):
            try:
                if isinstance(process_data['region'], str) and process_data['region'].isdigit():
                    region = Regions.objects.get(id=int(process_data['region']))
                elif hasattr(process_data['region'], 'region'):
                    region = process_data['region']
            except (Regions.DoesNotExist, ValueError):
                pass
        
        if process_data.get('section'):
            try:
                if hasattr(process_data['section'], 'section'):
                    section = process_data['section']
                else:
                    section = Sections.objects.filter(section=process_data['section']).first()
            except Exception:
                pass
        
        # Create process
        process = Process.objects.create(
            name=name,
            description=f"Migrated from {process_data.get('source', 'legacy system')}",
            department=department,
            region=region,
            section=section,
            is_active=True
        )
        
        return process

    def _migrate_process_documents(self, process: Process, process_data: Dict) -> int:
        """Migrate documents associated with a process."""
        documents_count = 0
        
        # For knowledge center folder files
        if process_data.get('source') == 'knowledge_center_folder':
            try:
                # Categorize the document
                doc_type, confidence = self.doc_service.categorize_document(
                    process_data['filename']
                )
                
                if doc_type and confidence > 0.25:
                    # Create process document record
                    ProcessDocument.objects.create(
                        process=process,
                        document_type=doc_type,
                        filename=process_data['filename'],
                        file=f"uploads/knowledge_center/{process_data['filename']}",
                        version='1.0',
                        is_current=True
                    )
                    documents_count += 1
                else:
                    self.migration_report['warnings'].append(
                        f'Could not categorize document: {process_data["filename"]}'
                    )
            except Exception as e:
                self.migration_report['errors'].append(
                    f'Error migrating document {process_data["filename"]}: {str(e)}'
                )
        
        # For legacy knowledge center data
        elif process_data.get('source') == 'legacy_knowledge_center':
            try:
                doc_type, confidence = self.doc_service.categorize_document(
                    process_data['filename'],
                    process_data.get('filetype', '')
                )
                
                if doc_type and confidence > 0.25:
                    ProcessDocument.objects.create(
                        process=process,
                        document_type=doc_type,
                        filename=process_data['filename'],
                        file=process_data.get('filepath', ''),
                        version='1.0',
                        is_current=True
                    )
                    documents_count += 1
            except Exception as e:
                self.migration_report['errors'].append(
                    f'Error migrating legacy document {process_data["filename"]}: {str(e)}'
                )
        
        return documents_count

    def _generate_analysis_report(self, analysis_result: Dict):
        """Generate and display analysis report."""
        self.stdout.write(self.style.SUCCESS('\n=== ANALYSIS REPORT ==='))
        self.stdout.write(f'Total processes found: {analysis_result["total_processes"]}')
        self.stdout.write(f'Processes by department:')
        
        for dept, processes in analysis_result['processes_by_department'].items():
            self.stdout.write(f'  {dept}: {len(processes)} processes')
        
        if analysis_result['unmapped_processes']:
            self.stdout.write(f'Unmapped processes: {len(analysis_result["unmapped_processes"])}')
        
        folder_analysis = self.folder_service.get_analysis_report()
        doc_analysis = self.doc_service.get_categorization_report()
        
        self.stdout.write(f'\nFolder Analysis:')
        self.stdout.write(f'  Folders analyzed: {folder_analysis["folders_analyzed"]}')
        self.stdout.write(f'  Processes identified: {folder_analysis["processes_identified"]}')
        
        if folder_analysis['mapping_errors']:
            self.stdout.write(f'  Mapping errors: {len(folder_analysis["mapping_errors"])}')

    def _generate_migration_report(self, output_file: Optional[str] = None):
        """Generate final migration report."""
        duration = None
        if self.migration_report['start_time'] and self.migration_report['end_time']:
            duration = self.migration_report['end_time'] - self.migration_report['start_time']
        
        report = {
            **self.migration_report,
            'duration_seconds': duration.total_seconds() if duration else None,
            'folder_analysis': self.folder_service.get_analysis_report(),
            'document_analysis': self.doc_service.get_categorization_report(),
        }
        
        # Display summary
        self.stdout.write(self.style.SUCCESS('\n=== MIGRATION REPORT ==='))
        self.stdout.write(f'Duration: {duration}' if duration else 'Duration: Unknown')
        self.stdout.write(f'Departments created: {report["departments_created"]}')
        self.stdout.write(f'Processes created: {report["total_processes_created"]}')
        self.stdout.write(f'Documents migrated: {report["total_documents_migrated"]}')
        
        if report['errors']:
            self.stdout.write(self.style.ERROR(f'Errors: {len(report["errors"])}'))
            for error in report['errors'][:5]:  # Show first 5 errors
                self.stdout.write(f'  - {error}')
            if len(report['errors']) > 5:
                self.stdout.write(f'  ... and {len(report["errors"]) - 5} more errors')
        
        if report['warnings']:
            self.stdout.write(self.style.WARNING(f'Warnings: {len(report["warnings"])}'))
        
        if report['skipped_items']:
            self.stdout.write(f'Skipped items: {len(report["skipped_items"])}')
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                self.stdout.write(f'Report saved to: {output_file}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to save report: {str(e)}')
                )
    
    def _validate_migration(self) -> Dict:
        """Validate migration prerequisites."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if departments already exist
        existing_depts = ProcessDepartment.objects.count()
        if existing_depts > 0:
            validation_result['warnings'].append(
                f'Found {existing_depts} existing departments'
            )
        
        # Check if processes already exist
        existing_processes = Process.objects.count()
        if existing_processes > 0:
            validation_result['warnings'].append(
                f'Found {existing_processes} existing processes'
            )
            validation_result['errors'].append(
                'Processes already exist. Use --force to override.'
            )
            validation_result['valid'] = False
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            validation_result['errors'].append(f'Database connection failed: {str(e)}')
            validation_result['valid'] = False
        
        # Check required models exist
        required_models = [ProcessDepartment, Process, ProcessDocument]
        for model in required_models:
            try:
                model._meta.get_field('id')
            except Exception as e:
                validation_result['errors'].append(
                    f'Model {model.__name__} not properly configured: {str(e)}'
                )
                validation_result['valid'] = False
        
        self.migration_report['validation_results'] = validation_result
        return validation_result

    def _display_validation_results(self, validation_result: Dict):
        """Display validation results."""
        self.stdout.write(self.style.SUCCESS('\n=== VALIDATION RESULTS ==='))
        
        if validation_result['valid']:
            self.stdout.write(self.style.SUCCESS('✓ Migration validation passed'))
        else:
            self.stdout.write(self.style.ERROR('✗ Migration validation failed'))
        
        if validation_result['errors']:
            self.stdout.write(self.style.ERROR('Errors:'))
            for error in validation_result['errors']:
                self.stdout.write(f'  - {error}')
        
        if validation_result['warnings']:
            self.stdout.write(self.style.WARNING('Warnings:'))
            for warning in validation_result['warnings']:
                self.stdout.write(f'  - {warning}')

    def _execute_dry_run_migration(self, analysis_result: Dict):
        """Execute migration in dry-run mode."""
        self.stdout.write(self.style.SUCCESS('\n=== DRY RUN MODE ==='))
        
        # Step 1: Create departments (dry run)
        self.stdout.write('Creating departments...')
        self._create_departments(dry_run=True)
        
        # Step 2: Migrate processes (dry run)
        self.stdout.write('Migrating processes...')
        self._migrate_processes(analysis_result, dry_run=True)
        
        self.stdout.write(self.style.SUCCESS('Dry run completed - no changes made'))

    def _execute_migration_with_rollback(self, analysis_result: Dict):
        """Execute migration with rollback support."""
        rollback_data = {
            'timestamp': timezone.now(),
            'created_objects': {
                'departments': [],
                'processes': [],
                'documents': []
            }
        }
        
        try:
            with transaction.atomic():
                # Create savepoint for rollback
                savepoint = transaction.savepoint()
                
                # Step 1: Create departments
                self.stdout.write('Creating departments...')
                dept_count_before = ProcessDepartment.objects.count()
                self._create_departments(dry_run=False)
                dept_count_after = ProcessDepartment.objects.count()
                
                # Track created departments
                if dept_count_after > dept_count_before:
                    new_depts = ProcessDepartment.objects.all()[dept_count_before:]
                    rollback_data['created_objects']['departments'] = [
                        dept.id for dept in new_depts
                    ]
                
                # Step 2: Migrate processes
                self.stdout.write('Migrating processes...')
                process_count_before = Process.objects.count()
                doc_count_before = ProcessDocument.objects.count()
                
                self._migrate_processes(analysis_result, dry_run=False)
                
                process_count_after = Process.objects.count()
                doc_count_after = ProcessDocument.objects.count()
                
                # Track created objects
                if process_count_after > process_count_before:
                    new_processes = Process.objects.all()[process_count_before:]
                    rollback_data['created_objects']['processes'] = [
                        proc.id for proc in new_processes
                    ]
                
                if doc_count_after > doc_count_before:
                    new_docs = ProcessDocument.objects.all()[doc_count_before:]
                    rollback_data['created_objects']['documents'] = [
                        doc.id for doc in new_docs
                    ]
                
                # Save rollback information
                self.migration_report['rollback_info'] = rollback_data
                
                # If we get here, commit the transaction
                transaction.savepoint_commit(savepoint)
                
        except Exception as e:
            # Rollback on error
            transaction.savepoint_rollback(savepoint)
            raise e

    def _handle_rollback(self):
        """Handle rollback request."""
        self.stdout.write(self.style.WARNING('Starting rollback process...'))
        
        # Check if there's rollback information
        rollback_info = self.migration_report.get('rollback_info')
        if not rollback_info:
            self.stdout.write(
                self.style.ERROR('No rollback information found. Cannot rollback.')
            )
            return
        
        try:
            self._rollback_migration(rollback_info)
            self.stdout.write(self.style.SUCCESS('Rollback completed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Rollback failed: {str(e)}'))
            raise CommandError(f'Rollback failed: {str(e)}')

    def _rollback_migration(self, rollback_info: Optional[Dict] = None):
        """Rollback migration changes."""
        if not rollback_info:
            rollback_info = self.migration_report.get('rollback_info', {})
        
        created_objects = rollback_info.get('created_objects', {})
        
        with transaction.atomic():
            # Remove created documents
            if created_objects.get('documents'):
                doc_count = ProcessDocument.objects.filter(
                    id__in=created_objects['documents']
                ).delete()[0]
                self.stdout.write(f'Removed {doc_count} documents')
            
            # Remove created processes
            if created_objects.get('processes'):
                proc_count = Process.objects.filter(
                    id__in=created_objects['processes']
                ).delete()[0]
                self.stdout.write(f'Removed {proc_count} processes')
            
            # Remove created departments (be careful here)
            if created_objects.get('departments'):
                dept_count = ProcessDepartment.objects.filter(
                    id__in=created_objects['departments']
                ).delete()[0]
                self.stdout.write(f'Removed {dept_count} departments')

    def _show_progress(self, message: str, current: int = 0, total: int = 0):
        """Show progress information."""
        if total > 0:
            percentage = (current / total) * 100
            self.stdout.write(f'[{percentage:.1f}%] {message}')
        else:
            self.stdout.write(f'[INFO] {message}')
 