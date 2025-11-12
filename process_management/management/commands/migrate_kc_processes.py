"""
Django management command for migrating processes from Knowledge Center to Process Management.

Usage:
    python manage.py migrate_kc_processes [options]

Examples:
    # Dry run to see what would be migrated
    python manage.py migrate_kc_processes --dry-run
    
    # Migrate specific department
    python manage.py migrate_kc_processes --department="Engineering"
    
    # Full migration with custom batch size
    python manage.py migrate_kc_processes --batch-size=50
    
    # Resume failed migration
    python manage.py migrate_kc_processes --resume=migration_20241201_143022_abc12345
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from process_management.knowledge_center_migrator import KnowledgeCenterMigrator
from process_management.models import ProcessDepartment


class Command(BaseCommand):
    help = 'Migrate processes from Knowledge Center to Process Management system'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        
        # Migration mode options
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without making any changes'
        )
        
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only analyze KC data and show what would be migrated'
        )
        
        # Filtering options
        parser.add_argument(
            '--department',
            type=str,
            help='Migrate only processes from specific department'
        )
        
        parser.add_argument(
            '--folder-id',
            type=int,
            help='Migrate only processes from specific KC folder ID'
        )
        
        parser.add_argument(
            '--app-id',
            type=int,
            default=2,
            help='Knowledge Center application ID to migrate (default: 2)'
        )
        
        # Processing options
        parser.add_argument(
            '--batch-size',
            type=int,
            default=25,
            help='Number of processes to migrate in each batch (default: 25)'
        )
        
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retry attempts for failed items (default: 3)'
        )
        
        # Resume and recovery options
        parser.add_argument(
            '--resume',
            type=str,
            help='Resume migration from checkpoint (provide migration ID)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if validation warnings exist'
        )
        
        # Output options
        parser.add_argument(
            '--output-file',
            type=str,
            help='Save migration results to JSON file'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        """Execute the migration command."""
        
        try:
            # Set up logging level
            if options['verbose']:
                import logging
                logging.getLogger('process_management').setLevel(logging.DEBUG)
            
            # Validate options
            self._validate_options(options)
            
            # Initialize migrator
            migration_id = options.get('resume')
            migrator = KnowledgeCenterMigrator(migration_id=migration_id)
            
            # Build configuration
            config = self._build_config(options)
            
            # Execute based on mode
            if options['analyze_only']:
                results = self._analyze_only(migrator, config)
            elif options['resume']:
                results = self._resume_migration(migrator, config)
            else:
                results = self._execute_migration(migrator, config)
            
            # Display results
            self._display_results(results, options)
            
            # Save results to file if requested
            if options.get('output_file'):
                self._save_results_to_file(results, options['output_file'])
            
            # Set exit code based on success
            if not results.get('success', False):
                raise CommandError(f"Migration failed: {results.get('error', 'Unknown error')}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Migration command failed: {str(e)}')
            )
            raise CommandError(str(e))
    
    def _validate_options(self, options):
        """Validate command line options."""
        
        # Check for conflicting options
        if options['dry_run'] and options['resume']:
            raise CommandError("Cannot use --dry-run with --resume")
        
        if options['analyze_only'] and options['resume']:
            raise CommandError("Cannot use --analyze-only with --resume")
        
        # Validate batch size
        if options['batch_size'] < 1 or options['batch_size'] > 1000:
            raise CommandError("Batch size must be between 1 and 1000")
        
        # Validate max retries
        if options['max_retries'] < 0 or options['max_retries'] > 10:
            raise CommandError("Max retries must be between 0 and 10")
        
        # Check if resume migration exists
        if options['resume']:
            from process_management.models import MigrationCheckpoint
            if not MigrationCheckpoint.objects.filter(migration_id=options['resume']).exists():
                raise CommandError(f"Migration checkpoint '{options['resume']}' not found")
    
    def _build_config(self, options):
        """Build migration configuration from options."""
        
        config = {
            'dry_run': options['dry_run'],
            'batch_size': options['batch_size'],
            'max_retries': options['max_retries'],
            'force': options['force'],
            'verbose': options['verbose']
        }
        
        # Add filtering options
        if options.get('department'):
            config['department_filter'] = options['department']
        
        if options.get('folder_id'):
            config['folder_id_filter'] = options['folder_id']
        
        if options.get('app_id'):
            config['app_id'] = options['app_id']
        
        return config
    
    def _analyze_only(self, migrator, config):
        """Perform analysis only without migration."""
        
        self.stdout.write("Analyzing Knowledge Center data...")
        
        # Get process candidates
        app_id = config.get('app_id', 2)
        candidates = migrator.analyzer.analyze_kc_processes(app_id)
        
        if not candidates:
            self.stdout.write(
                self.style.WARNING("No process candidates found in Knowledge Center")
            )
            return {'success': True, 'candidates': []}
        
        # Analyze candidates
        analysis = {
            'total_candidates': len(candidates),
            'departments': {},
            'document_types': {},
            'potential_issues': []
        }
        
        for candidate in candidates:
            # Count by department
            dept = candidate.department_name
            if dept not in analysis['departments']:
                analysis['departments'][dept] = 0
            analysis['departments'][dept] += 1
            
            # Count document types
            for file_data in candidate.files:
                doc_type = file_data.get('document_type', 'unclassified')
                if doc_type not in analysis['document_types']:
                    analysis['document_types'][doc_type] = 0
                analysis['document_types'][doc_type] += 1
            
            # Check for issues
            if not candidate.files:
                analysis['potential_issues'].append(
                    f"Process '{candidate.process_name}' has no files"
                )
            
            if len(candidate.process_name) < 3:
                analysis['potential_issues'].append(
                    f"Process name too short: '{candidate.process_name}'"
                )
        
        return {
            'success': True,
            'analysis_only': True,
            'analysis': analysis,
            'candidates': [c.__dict__ for c in candidates]
        }
    
    def _resume_migration(self, migrator, config):
        """Resume a previously failed migration."""
        
        self.stdout.write(f"Resuming migration: {config.get('resume')}")
        
        # Get migration status
        status = migrator.get_migration_status(config['resume'])
        
        if 'error' in status:
            raise CommandError(f"Cannot resume migration: {status['error']}")
        
        if not status.get('can_resume', False):
            raise CommandError("Migration cannot be resumed (already completed or no resume data)")
        
        # Execute resumed migration
        return migrator.migrate_processes(config)
    
    def _execute_migration(self, migrator, config):
        """Execute the migration."""
        
        mode = "DRY RUN" if config['dry_run'] else "LIVE"
        self.stdout.write(f"Starting Knowledge Center migration ({mode})...")
        
        # Pre-migration checks
        if not config['force']:
            self._perform_pre_migration_checks()
        
        # Execute migration
        results = migrator.migrate_processes(config)
        
        return results
    
    def _perform_pre_migration_checks(self):
        """Perform pre-migration validation checks."""
        
        self.stdout.write("Performing pre-migration checks...")
        
        checks = []
        
        # Check if process management tables exist
        try:
            ProcessDepartment.objects.count()
            checks.append(("Process Management tables", True, "OK"))
        except Exception as e:
            checks.append(("Process Management tables", False, str(e)))
        
        # Check Knowledge Center data access
        try:
            from knowledge_center.models import FolderApplication
            pp_app = FolderApplication.objects.filter(id=2).first()
            if pp_app:
                checks.append(("Knowledge Center access", True, "OK"))
            else:
                checks.append(("Knowledge Center access", False, "PROCESSES AND PROCEDURES app not found"))
        except Exception as e:
            checks.append(("Knowledge Center access", False, str(e)))
        
        # Check file system permissions
        try:
            from django.conf import settings
            import os
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'processes')
            os.makedirs(upload_dir, exist_ok=True)
            checks.append(("File system permissions", True, "OK"))
        except Exception as e:
            checks.append(("File system permissions", False, str(e)))
        
        # Display check results
        failed_checks = []
        for check_name, passed, message in checks:
            if passed:
                self.stdout.write(f"  ✓ {check_name}: {message}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {check_name}: {message}")
                )
                failed_checks.append(check_name)
        
        if failed_checks:
            raise CommandError(
                f"Pre-migration checks failed: {', '.join(failed_checks)}. "
                "Use --force to override."
            )
    
    def _display_results(self, results, options):
        """Display migration results."""
        
        if results.get('analysis_only'):
            self._display_analysis_results(results)
        elif results.get('dry_run'):
            self._display_dry_run_results(results)
        else:
            self._display_migration_results(results)
    
    def _display_analysis_results(self, results):
        """Display analysis-only results."""
        
        analysis = results.get('analysis', {})
        
        self.stdout.write(
            self.style.SUCCESS(f"\nAnalysis Results:")
        )
        
        self.stdout.write(f"Total process candidates: {analysis.get('total_candidates', 0)}")
        
        # Department breakdown
        departments = analysis.get('departments', {})
        if departments:
            self.stdout.write("\nDepartment breakdown:")
            for dept, count in sorted(departments.items()):
                self.stdout.write(f"  {dept}: {count} processes")
        
        # Document type breakdown
        doc_types = analysis.get('document_types', {})
        if doc_types:
            self.stdout.write("\nDocument type breakdown:")
            for doc_type, count in sorted(doc_types.items()):
                self.stdout.write(f"  {doc_type}: {count} documents")
        
        # Potential issues
        issues = analysis.get('potential_issues', [])
        if issues:
            self.stdout.write(
                self.style.WARNING(f"\nPotential issues ({len(issues)}):")
            )
            for issue in issues[:10]:  # Show first 10 issues
                self.stdout.write(f"  - {issue}")
            if len(issues) > 10:
                self.stdout.write(f"  ... and {len(issues) - 10} more")
    
    def _display_dry_run_results(self, results):
        """Display dry run results."""
        
        stats = results.get('statistics', {})
        
        self.stdout.write(
            self.style.SUCCESS(f"\nDry Run Results:")
        )
        
        self.stdout.write(f"Total candidates: {stats.get('total_candidates', 0)}")
        self.stdout.write(f"Processes to create: {stats.get('processes_to_create', 0)}")
        self.stdout.write(f"Documents to create: {stats.get('documents_to_create', 0)}")
        
        # Departments to create
        new_depts = stats.get('departments_to_create', [])
        if new_depts:
            self.stdout.write(f"\nDepartments to create ({len(new_depts)}):")
            for dept in new_depts:
                self.stdout.write(f"  - {dept}")
        
        # Potential issues
        issues = stats.get('potential_issues', [])
        if issues:
            self.stdout.write(
                self.style.WARNING(f"\nPotential issues ({len(issues)}):")
            )
            for issue in issues[:10]:
                self.stdout.write(f"  - {issue}")
            if len(issues) > 10:
                self.stdout.write(f"  ... and {len(issues) - 10} more")
    
    def _display_migration_results(self, results):
        """Display actual migration results."""
        
        if results.get('success'):
            stats = results.get('statistics', {})
            
            self.stdout.write(
                self.style.SUCCESS(f"\nMigration completed successfully!")
            )
            
            self.stdout.write(f"Migration ID: {results.get('migration_id')}")
            self.stdout.write(f"Processes created: {stats.get('processes_created', 0)}")
            self.stdout.write(f"Documents created: {stats.get('documents_created', 0)}")
            self.stdout.write(f"Departments created: {stats.get('departments_created', 0)}")
            
            if stats.get('errors', 0) > 0:
                self.stdout.write(
                    self.style.WARNING(f"Errors encountered: {stats['errors']}")
                )
            
            if stats.get('skipped', 0) > 0:
                self.stdout.write(
                    self.style.WARNING(f"Items skipped: {stats['skipped']}")
                )
            
            # Processing summary
            processing_summary = results.get('processing_summary', {})
            if processing_summary:
                success_rate = processing_summary.get('success_rate', 0)
                total_time = processing_summary.get('total_processing_time', 0)
                
                self.stdout.write(f"\nProcessing Summary:")
                self.stdout.write(f"Success rate: {success_rate:.1f}%")
                self.stdout.write(f"Total time: {total_time:.2f} seconds")
                
                if processing_summary.get('items_per_second', 0) > 0:
                    self.stdout.write(f"Processing rate: {processing_summary['items_per_second']:.2f} items/second")
            
            # Failed items
            failed_items = results.get('failed_items', [])
            if failed_items:
                self.stdout.write(
                    self.style.WARNING(f"\nFailed items ({len(failed_items)}):")
                )
                for item in failed_items[:5]:  # Show first 5 failed items
                    self.stdout.write(f"  - {item.get('process_name', 'Unknown')}")
                if len(failed_items) > 5:
                    self.stdout.write(f"  ... and {len(failed_items) - 5} more")
        
        else:
            error = results.get('error', 'Unknown error')
            self.stdout.write(
                self.style.ERROR(f"\nMigration failed: {error}")
            )
            
            stats = results.get('statistics', {})
            if stats:
                self.stdout.write(f"Partial results:")
                self.stdout.write(f"  Processes created: {stats.get('processes_created', 0)}")
                self.stdout.write(f"  Documents created: {stats.get('documents_created', 0)}")
    
    def _save_results_to_file(self, results, filename):
        """Save migration results to JSON file."""
        
        try:
            # Convert datetime objects to strings for JSON serialization
            def json_serializer(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                return str(obj)
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=json_serializer)
            
            self.stdout.write(f"Results saved to: {filename}")
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Could not save results to file: {e}")
            )