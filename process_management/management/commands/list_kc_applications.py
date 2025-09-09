"""
Django management command for listing Knowledge Center applications.

This command helps identify available KC applications and their structure
before running the migration.

Usage:
    python manage.py list_kc_applications
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'List available Knowledge Center applications'
    
    def handle(self, *args, **options):
        """Execute the command."""
        
        try:
            from knowledge_center.models import FolderApplication, KnowledgeCentreFolder, KnowldgeCentreFile
            
            self.stdout.write("Available Knowledge Center Applications:")
            self.stdout.write("=" * 50)
            
            apps = FolderApplication.objects.all().order_by('id')
            
            if not apps.exists():
                self.stdout.write("No Knowledge Center applications found.")
                return
            
            for app in apps:
                self.stdout.write(f"\nID {app.id}: {app.name}")
                self.stdout.write(f"Created: {app.created_at}")
                
                # Count root folders
                root_folders = KnowledgeCentreFolder.objects.filter(
                    folder_application=app,
                    parent__isnull=True
                ).count()
                
                # Count total folders
                total_folders = KnowledgeCentreFolder.objects.filter(
                    folder_application=app
                ).count()
                
                # Count files
                total_files = KnowldgeCentreFile.objects.filter(
                    folder__folder_application=app,
                    archived=False
                ).count()
                
                archived_files = KnowldgeCentreFile.objects.filter(
                    folder__folder_application=app,
                    archived=True
                ).count()
                
                self.stdout.write(f"  Root folders: {root_folders}")
                self.stdout.write(f"  Total folders: {total_folders}")
                self.stdout.write(f"  Active files: {total_files}")
                self.stdout.write(f"  Archived files: {archived_files}")
                
                # List root folders
                if root_folders > 0:
                    self.stdout.write("  Root folder names:")
                    root_folder_objects = KnowledgeCentreFolder.objects.filter(
                        folder_application=app,
                        parent__isnull=True
                    ).order_by('name')[:10]  # Show first 10
                    
                    for folder in root_folder_objects:
                        files_in_folder = KnowldgeCentreFile.objects.filter(
                            folder=folder,
                            archived=False
                        ).count()
                        self.stdout.write(f"    - {folder.name} ({files_in_folder} files)")
                    
                    if root_folders > 10:
                        self.stdout.write(f"    ... and {root_folders - 10} more")
            
            self.stdout.write(f"\nTo analyze a specific application, use:")
            self.stdout.write(f"python manage.py analyze_kc_structure --app-id=<ID>")
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR("Knowledge Center models not available")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error listing applications: {str(e)}")
            )