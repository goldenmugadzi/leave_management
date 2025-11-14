"""
Test command for Knowledge Center migration.

This command tests the migration logic with your specific data structure
and provides detailed output about what would be migrated.
"""

from django.core.management.base import BaseCommand
from process_management.knowledge_center_migrator import ProcessCandidateAnalyzer, KnowledgeCenterMigrator


class Command(BaseCommand):
    help = 'Test Knowledge Center migration with your data structure'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--app-id',
            type=int,
            default=2,
            help='Knowledge Center application ID to test (default: 2)'
        )
        
        parser.add_argument(
            '--folder-id',
            type=int,
            help='Restrict analysis to a specific Knowledge Center folder ID'
        )
        
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Show detailed information about each process candidate'
        )
    
    def handle(self, *args, **options):
        """Execute the test."""
        
        try:
            app_id = options['app_id']
            
            self.stdout.write(f"Testing KC migration for application ID: {app_id}")
            self.stdout.write("=" * 60)
            
            # Test basic KC access
            self._test_kc_access(app_id, options.get('folder_id'))
            
            # Test migration logic
            self._test_migration_logic(app_id, options.get('folder_id'), options['show_details'])
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Test failed: {str(e)}")
            )
    
    def _test_kc_access(self, app_id, folder_id):
        """Test basic Knowledge Center access."""
        
        try:
            from knowledge_center.models import FolderApplication, KnowledgeCentreFolder, KnowldgeCentreFile
            
            self.stdout.write("1. Testing Knowledge Center access...")
            
            # List all applications
            apps = FolderApplication.objects.all()
            self.stdout.write(f"   Found {apps.count()} applications:")
            
            for app in apps:
                folders = KnowledgeCentreFolder.objects.filter(folder_application=app).count()
                files = KnowldgeCentreFile.objects.filter(folder__folder_application=app).count()
                self.stdout.write(f"     ID {app.id}: {app.name} ({folders} folders, {files} files)")
            
            # Test specific application
            target_app = FolderApplication.objects.filter(id=app_id).first()
            if target_app:
                self.stdout.write(f"\n2. Analyzing target application: {target_app.name}")
                
                # Root folders
                root_folders = KnowledgeCentreFolder.objects.filter(
                    folder_application=target_app,
                    parent__isnull=True
                )
                self.stdout.write(f"   Root folders: {root_folders.count()}")
                
                # All folders
                all_folders = KnowledgeCentreFolder.objects.filter(
                    folder_application=target_app
                )
                self.stdout.write(f"   Total folders: {all_folders.count()}")
                
                # Files
                active_files = KnowldgeCentreFile.objects.filter(
                    folder__folder_application=target_app,
                    archived=False
                ).count()
                
                archived_files = KnowldgeCentreFile.objects.filter(
                    folder__folder_application=target_app,
                    archived=True
                ).count()
                
                self.stdout.write(f"   Active files: {active_files}")
                self.stdout.write(f"   Archived files: {archived_files}")
                
                # Show some folder names
                if all_folders.exists():
                    self.stdout.write("   Sample folders:")
                    for folder in all_folders[:5]:
                        files_count = KnowldgeCentreFile.objects.filter(
                            folder=folder,
                            archived=False
                        ).count()
                        parent_info = f" (parent: {folder.parent.name})" if folder.parent else " (root)"
                        self.stdout.write(f"     - {folder.name}{parent_info} ({files_count} files)")
                if folder_id:
                    target_folder = KnowledgeCentreFolder.objects.filter(id=folder_id).first()
                    if target_folder:
                        self.stdout.write(f"\n   Target folder (ID {folder_id}): {target_folder.name}")
                        self.stdout.write(f"   Folder path: {self._build_folder_path(target_folder)}")
                        files_count = KnowldgeCentreFile.objects.filter(folder=target_folder, archived=False).count()
                        self.stdout.write(f"   Files in target folder: {files_count}")
                    else:
                        self.stdout.write(self.style.WARNING(f"\n   Folder ID {folder_id} not found"))
            else:
                self.stdout.write(f"   ERROR: Application ID {app_id} not found!")
                return False
            
            return True
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR("   ERROR: Cannot import Knowledge Center models")
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ERROR: {str(e)}")
            )
            return False
    
    def _test_migration_logic(self, app_id, folder_id, show_details):
        """Test the migration logic."""
        
        self.stdout.write(f"\n3. Testing migration logic...")
        
        try:
            # Create analyzer
            analyzer = ProcessCandidateAnalyzer()
            
            # Analyze processes
            candidates = analyzer.analyze_kc_processes(app_id, folder_id=folder_id)
            
            self.stdout.write(f"   Found {len(candidates)} process candidates")
            
            if not candidates:
                self.stdout.write("   No process candidates found. This could mean:")
                self.stdout.write("     - The application has no folders with files")
                self.stdout.write("     - The folders don't match process detection criteria")
                self.stdout.write("     - The files don't match document type patterns")
                return
            
            # Analyze candidates by department
            dept_counts = {}
            doc_type_counts = {}
            
            for candidate in candidates:
                dept = candidate.department_name
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                
                for file_data in candidate.files:
                    doc_type = file_data.get('document_type') or 'unclassified'
                    doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
            
            # Show summary
            self.stdout.write(f"\n   Department distribution:")
            for dept, count in sorted(dept_counts.items()):
                self.stdout.write(f"     {dept}: {count} processes")
            
            self.stdout.write(f"\n   Document type distribution:")
            for doc_type, count in sorted(doc_type_counts.items()):
                self.stdout.write(f"     {doc_type}: {count} documents")
            
            # Show details if requested
            if show_details:
                self.stdout.write(f"\n   Process candidates (showing first 10):")
                for i, candidate in enumerate(candidates[:10], 1):
                    self.stdout.write(f"     {i}. {candidate.process_name}")
                    self.stdout.write(f"        Department: {candidate.department_name}")
                    self.stdout.write(f"        Folder: {candidate.folder_name}")
                    self.stdout.write(f"        Files: {len(candidate.files)}")
                    
                    if candidate.files:
                        classified_files = [f for f in candidate.files if f.get('document_type')]
                        self.stdout.write(f"        Classified documents: {len(classified_files)}")
                        
                        for file_data in candidate.files[:3]:  # Show first 3 files
                            doc_type = file_data.get('document_type', 'unclassified')
                            self.stdout.write(f"          - {file_data['filename']} ({doc_type})")
                
                if len(candidates) > 10:
                    self.stdout.write(f"     ... and {len(candidates) - 10} more")
            
            # Test migration simulation
            self.stdout.write(f"\n4. Testing migration simulation...")
            
            migrator = KnowledgeCenterMigrator()
            
            # Dry run
            config = {
                'dry_run': True,
                'app_id': app_id
            }
            if folder_id:
                config['folder_id_filter'] = folder_id
            results = migrator.migrate_processes(config)
            
            if results.get('success'):
                stats = results.get('statistics', {})
                self.stdout.write(f"   Dry run successful!")
                self.stdout.write(f"   Would create {stats.get('processes_to_create', 0)} processes")
                self.stdout.write(f"   Would create {stats.get('documents_to_create', 0)} documents")
                
                new_depts = stats.get('departments_to_create', [])
                if new_depts:
                    self.stdout.write(f"   Would create {len(new_depts)} new departments:")
                    for dept in new_depts[:5]:
                        self.stdout.write(f"     - {dept}")
                    if len(new_depts) > 5:
                        self.stdout.write(f"     ... and {len(new_depts) - 5} more")
            else:
                error = results.get('error', 'Unknown error')
                self.stdout.write(
                    self.style.ERROR(f"   Dry run failed: {error}")
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   Migration logic test failed: {str(e)}")
            )
    
    def _build_folder_path(self, folder):
        """Helper to display full folder path."""
        parts = []
        current = folder
        while current:
            parts.append(current.name)
            current = current.parent
        return " > ".join(reversed(parts))