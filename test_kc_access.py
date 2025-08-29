#!/usr/bin/env python
"""
Simple test script to check Knowledge Center data access.
Run this to verify we can access your KC data structure.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/var/www/beii_v1')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

try:
    django.setup()
    
    print("Django setup successful!")
    
    # Test KC model access
    try:
        from knowledge_center.models import FolderApplication, KnowledgeCentreFolder, KnowldgeCentreFile
        
        print("\nKnowledge Center Applications:")
        apps = FolderApplication.objects.all()
        for app in apps:
            print(f"  ID {app.id}: {app.name}")
            
            # Count folders and files
            folders = KnowledgeCentreFolder.objects.filter(folder_application=app).count()
            files = KnowldgeCentreFile.objects.filter(folder__folder_application=app).count()
            print(f"    Folders: {folders}, Files: {files}")
        
        # Test specific app (ID 2)
        print(f"\nAnalyzing Application ID 2:")
        app2 = FolderApplication.objects.filter(id=2).first()
        if app2:
            print(f"  Name: {app2.name}")
            
            root_folders = KnowledgeCentreFolder.objects.filter(
                folder_application=app2,
                parent__isnull=True
            )
            
            print(f"  Root folders ({root_folders.count()}):")
            for folder in root_folders[:5]:  # Show first 5
                files_count = KnowldgeCentreFile.objects.filter(
                    folder=folder,
                    archived=False
                ).count()
                print(f"    - {folder.name} ({files_count} files)")
        else:
            print("  Application ID 2 not found!")
            
    except Exception as e:
        print(f"Error accessing KC models: {e}")
        
except Exception as e:
    print(f"Django setup failed: {e}")
    print("Make sure you're in the correct directory and dependencies are installed.")