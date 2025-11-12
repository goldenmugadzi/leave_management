"""
Knowledge Center to Process Management Migration System

This module provides comprehensive migration capabilities to move processes
from the Knowledge Center's "PROCESSES AND PROCEDURES" application to the
new Process Management system.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone
from django.core.files import File
from django.core.files.storage import default_storage

from .models import ProcessDepartment, Process, ProcessDocument
from .migration_infrastructure import (
    ProgressTracker, ErrorRecoveryManager, BatchProcessor, 
    CheckpointManager, ProcessingItem, ProcessingStatus
)


@dataclass
class ProcessCandidate:
    """Represents a potential process identified in the Knowledge Center."""
    folder_id: int
    folder_name: str
    folder_path: str
    department_name: str
    process_name: str
    description: str
    files: List[Dict[str, Any]]
    region: Optional[Any] = None
    section: Optional[Any] = None
    created_by: Optional[Any] = None
    metadata: Dict[str, Any] = None


class ProcessCandidateAnalyzer:
    """
    Analyzes Knowledge Center data to identify process candidates.
    
    Provides intelligent analysis of folder structures and files to
    identify processes and classify documents appropriately.
    """
    
    # Department mapping from KC folders to Process Management departments
    # Based on your organizational structure shown in the images
    DEPARTMENT_MAPPING = {
        'commercial': 'Commercial Operations',
        'engineering': 'Engineering',
        'engineering instructions': 'Engineering',
        'finance': 'Finance',
        'human resources': 'Human Resources',
        'hr': 'Human Resources',
        'ict': 'Information Communication Technology',
        'it': 'Information Communication Technology',
        'information communication technology': 'Information Communication Technology',
        'information technology': 'Information Communication Technology',
        'management': 'Management Processes',
        'management processes': 'Management Processes',
        'executive': 'Management Processes',
        'operations': 'Operations',
        'procurement': 'Procurement',
        'risk management': 'Risk Management',
        'risk': 'Risk Management',
        'safety': 'Safety and Health',
        'safety and health': 'Safety and Health',
        'legal': 'Legal Services',
        'legal services': 'Legal Services',
        'compliance': 'Legal Services',
        'legislation': 'Legal Services',
        'stakeholder relations': 'Stakeholder Relations',
        'stakeholder': 'Stakeholder Relations',
        'policies': 'Management Processes',
        'guidelines': 'Management Processes',
        'policies & guidelines': 'Management Processes',
        'standards': 'Quality Assurance',
        'specifications': 'Engineering',
        'drawings': 'Engineering',
        'manuals': 'Operations',
        'user manuals': 'Operations',
        'audit': 'Internal Audit',
        'quality': 'Quality Assurance',
        'planning': 'Strategic Planning',
        'prince2': 'Strategic Planning',
        'drone technology': 'Engineering',
        # Folder-specific mappings
        'processes interactions': 'Management Processes',
        'process maps': 'Management Processes',
        'procedures and work instructions': 'Operations',
        'process forms': 'Operations',
        'registers': 'Risk Management',
        'context of the organisation': 'Management Processes'
    }
    
    # Document type classification patterns
    # Updated based on your folder structure
    DOCUMENT_TYPE_PATTERNS = {
        'process_map': [
            r'.*process.*map.*',
            r'.*flowchart.*',
            r'.*workflow.*',
            r'.*diagram.*',
            r'.*flow.*chart.*',
            r'.*process.*flow.*',
            r'.*interaction.*',
            r'.*map.*'
        ],
        'procedure': [
            r'.*procedure.*',
            r'.*sop.*',
            r'.*standard.*operating.*',
            r'.*instruction.*',
            r'.*manual.*',
            r'.*guideline.*',
            r'.*policy.*',
            r'.*work.*instruction.*',
            r'.*form.*',
            r'.*template.*'
        ],
        'risk_register': [
            r'.*risk.*register.*',
            r'.*risk.*assessment.*',
            r'.*opportunity.*register.*',
            r'.*risk.*matrix.*',
            r'.*risk.*analysis.*',
            r'.*hazard.*register.*',
            r'.*register.*'
        ]
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_kc_processes(self, app_id: int = 2) -> List[ProcessCandidate]:
        """
        Analyze Knowledge Center data to identify process candidates.
        
        Returns:
            List of ProcessCandidate objects
        """
        try:
            from knowledge_center.models import KnowledgeCentreFolder, KnowldgeCentreFile, FolderApplication
            
            # Get process-related application
            pp_app = FolderApplication.objects.filter(id=app_id).first()
            if not pp_app:
                self.logger.error(f"Process-related application (ID={app_id}) not found")
                
                # Try to find any application with process-related content
                all_apps = FolderApplication.objects.all()
                self.logger.info("Available applications:")
                for app in all_apps:
                    folder_count = KnowledgeCentreFolder.objects.filter(folder_application=app).count()
                    self.logger.info(f"  ID {app.id}: {app.name} ({folder_count} folders)")
                
                return []
            
            self.logger.info(f"Analyzing processes in application: {pp_app.name}")
            
            # Get root folders for processes and procedures
            root_folders = KnowledgeCentreFolder.objects.filter(
                folder_application=pp_app,
                parent__isnull=True
            ).order_by('name')
            
            if not root_folders.exists():
                self.logger.warning(f"No root folders found in application {pp_app.name}")
                
                # Check if there are any folders at all in this application
                all_folders = KnowledgeCentreFolder.objects.filter(folder_application=pp_app)
                if all_folders.exists():
                    self.logger.info(f"Found {all_folders.count()} folders (not root level) in {pp_app.name}")
                    # Analyze all folders, not just root ones
                    root_folders = all_folders
                else:
                    self.logger.warning(f"No folders found at all in application {pp_app.name}")
                    return []
            
            process_candidates = []
            
            for root_folder in root_folders:
                candidates = self._analyze_folder_hierarchy(root_folder)
                process_candidates.extend(candidates)
            
            self.logger.info(f"Identified {len(process_candidates)} process candidates")
            return process_candidates
            
        except Exception as e:
            self.logger.error(f"Error analyzing KC processes: {e}")
            return []
    
    def _analyze_folder_hierarchy(self, folder) -> List[ProcessCandidate]:
        """
        Analyze a folder hierarchy to identify processes.
        
        Args:
            folder: KnowledgeCentreFolder instance
            
        Returns:
            List of ProcessCandidate objects found in this hierarchy
        """
        candidates = []
        
        try:
            from knowledge_center.models import KnowldgeCentreFile
            
            # Check if this folder contains files (potential process)
            files = KnowldgeCentreFile.objects.filter(
                folder=folder,
                archived=False
            ).order_by('filename')
            
            if files.exists():
                # This folder contains files, analyze as potential process
                candidate = self._create_process_candidate(folder, files)
                if candidate:
                    candidates.append(candidate)
            
            # Recursively analyze subfolders
            subfolders = folder.subfolders.all().order_by('name')
            for subfolder in subfolders:
                sub_candidates = self._analyze_folder_hierarchy(subfolder)
                candidates.extend(sub_candidates)
                
        except Exception as e:
            self.logger.error(f"Error analyzing folder {folder.name}: {e}")
        
        return candidates
    
    def _create_process_candidate(self, folder, files) -> Optional[ProcessCandidate]:
        """
        Create a ProcessCandidate from a folder and its files.
        
        Args:
            folder: KnowledgeCentreFolder instance
            files: QuerySet of KnowldgeCentreFile instances
            
        Returns:
            ProcessCandidate or None if not a valid process
        """
        try:
            # Build folder path
            folder_path = self._build_folder_path(folder)
            
            # Determine department from folder hierarchy
            department_name = self._determine_department(folder_path, folder.name)
            
            # Extract process name
            process_name = self._extract_process_name(folder, folder_path)
            
            # Classify files
            classified_files = []
            for file in files:
                file_data = {
                    'id': file.id,
                    'filename': file.filename,
                    'file_path': file.file.name if file.file else '',
                    'document_type': self._classify_document_type(file.filename),
                    'region': file.region,
                    'section': file.section,
                    'created_by': file.created_by,
                    'created_on': file.created_on,
                    'file_size': self._get_file_size(file),
                    'original_file': file
                }
                classified_files.append(file_data)
            
            # Only create candidate if we have at least one classifiable document
            if any(f['document_type'] for f in classified_files):
                return ProcessCandidate(
                    folder_id=folder.id,
                    folder_name=folder.name,
                    folder_path=folder_path,
                    department_name=department_name,
                    process_name=process_name,
                    description=self._generate_description(folder, classified_files),
                    files=classified_files,
                    region=self._get_common_region(files),
                    section=self._get_common_section(files),
                    created_by=self._get_common_creator(files),
                    metadata={
                        'original_folder_id': folder.id,
                        'file_count': len(classified_files),
                        'document_types': list(set(f['document_type'] for f in classified_files if f['document_type']))
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error creating process candidate for folder {folder.name}: {e}")
        
        return None
    
    def _build_folder_path(self, folder) -> str:
        """Build the full path of a folder."""
        path_parts = []
        current = folder
        
        while current:
            path_parts.append(current.name)
            current = current.parent
        
        path_parts.reverse()
        return ' > '.join(path_parts)
    
    def _determine_department(self, folder_path: str, folder_name: str) -> str:
        """
        Determine the department based on folder path and name.
        
        Args:
            folder_path: Full folder path
            folder_name: Current folder name
            
        Returns:
            Department name
        """
        # Check folder path for department keywords
        path_lower = folder_path.lower()
        name_lower = folder_name.lower()
        
        for keyword, department in self.DEPARTMENT_MAPPING.items():
            if keyword in path_lower or keyword in name_lower:
                return department
        
        # Default department if no match found
        return 'General Operations'
    
    def _extract_process_name(self, folder, folder_path: str) -> str:
        """
        Extract a clean process name from folder information.
        
        Args:
            folder: KnowledgeCentreFolder instance
            folder_path: Full folder path
            
        Returns:
            Clean process name
        """
        # Start with folder name
        process_name = folder.name
        
        # Clean up common prefixes/suffixes
        cleanup_patterns = [
            r'^(process|procedure|sop|manual|guideline|policy)\s*[-_:]?\s*',
            r'\s*(process|procedure|sop|manual|guideline|policy)$',
            r'^\d+\.\s*',  # Remove leading numbers
            r'^[A-Z]+\d+\s*[-_:]?\s*',  # Remove codes like "ENG01:"
        ]
        
        for pattern in cleanup_patterns:
            process_name = re.sub(pattern, '', process_name, flags=re.IGNORECASE)
        
        # Capitalize properly
        process_name = process_name.strip().title()
        
        # If name is too short or generic, use parent folder context
        if len(process_name) < 3 or process_name.lower() in ['files', 'documents', 'misc', 'other']:
            if folder.parent:
                parent_name = folder.parent.name
                process_name = f"{parent_name} - {process_name}"
        
        return process_name or "Unnamed Process"
    
    def _classify_document_type(self, filename: str) -> Optional[str]:
        """
        Classify a document based on its filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            Document type ('process_map', 'procedure', 'risk_register') or None
        """
        filename_lower = filename.lower()
        
        for doc_type, patterns in self.DOCUMENT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return doc_type
        
        return None
    
    def _generate_description(self, folder, files: List[Dict]) -> str:
        """Generate a description for the process."""
        doc_types = [f['document_type'] for f in files if f['document_type']]
        doc_type_counts = {}
        for doc_type in doc_types:
            doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
        
        description_parts = [f"Process migrated from Knowledge Center folder: {folder.name}"]
        
        if doc_type_counts:
            type_descriptions = []
            for doc_type, count in doc_type_counts.items():
                type_name = doc_type.replace('_', ' ').title()
                type_descriptions.append(f"{count} {type_name}{'s' if count > 1 else ''}")
            description_parts.append(f"Contains: {', '.join(type_descriptions)}")
        
        return '. '.join(description_parts)
    
    def _get_file_size(self, file) -> int:
        """Get file size safely."""
        try:
            if file.file and hasattr(file.file, 'size'):
                return file.file.size
        except:
            pass
        return 0
    
    def _get_common_region(self, files):
        """Get the most common region from files."""
        regions = [f.region for f in files if f.region]
        if regions:
            return max(set(regions), key=regions.count)
        return None
    
    def _get_common_section(self, files):
        """Get the most common section from files."""
        sections = [f.section for f in files if f.section]
        if sections:
            return max(set(sections), key=sections.count)
        return None
    
    def _get_common_creator(self, files):
        """Get the most common creator from files."""
        creators = [f.created_by for f in files if f.created_by]
        if creators:
            return max(set(creators), key=creators.count)
        return None


class KnowledgeCenterMigrator:
    """
    Main migration class for moving processes from Knowledge Center to Process Management.
    
    Provides comprehensive migration with error handling, progress tracking,
    and resume capability.
    """
    
    def __init__(self, migration_id: str = None):
        """
        Initialize the migrator.
        
        Args:
            migration_id: Optional migration ID for resume capability
        """
        self.migration_id = migration_id
        self.checkpoint_manager = CheckpointManager(migration_id)
        self.analyzer = ProcessCandidateAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # Migration statistics
        self.stats = {
            'total_candidates': 0,
            'processes_created': 0,
            'documents_created': 0,
            'departments_created': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def migrate_processes(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the complete migration process.
        
        Args:
            config: Migration configuration options
            
        Returns:
            Migration results dictionary
        """
        config = config or {}
        
        try:
            self.logger.info("Starting Knowledge Center to Process Management migration")
            
            # Step 1: Analyze KC data
            self.logger.info("Step 1: Analyzing Knowledge Center data...")
            app_id = config.get('app_id', 2)
            process_candidates = self.analyzer.analyze_kc_processes(app_id)
            
            if not process_candidates:
                self.logger.warning("No process candidates found in Knowledge Center")
                return {'success': False, 'message': 'No processes found to migrate'}
            
            self.stats['total_candidates'] = len(process_candidates)
            
            # Step 2: Set up migration infrastructure
            self.logger.info(f"Step 2: Setting up migration for {len(process_candidates)} candidates...")
            
            progress_tracker = ProgressTracker(
                total_items=len(process_candidates),
                description="Migrating KC Processes"
            )
            
            error_manager = ErrorRecoveryManager(
                max_retries=config.get('max_retries', 3)
            )
            
            batch_processor = BatchProcessor(
                batch_size=config.get('batch_size', 25),
                progress_tracker=progress_tracker,
                error_manager=error_manager
            )
            
            # Step 3: Create checkpoint
            checkpoint = self.checkpoint_manager.create_checkpoint(
                total_items=len(process_candidates),
                config=config
            )
            
            # Step 4: Convert candidates to processing items
            processing_items = []
            for candidate in process_candidates:
                item = ProcessingItem(
                    id=f"process_{candidate.folder_id}",
                    data=candidate.__dict__
                )
                processing_items.append(item)
            
            # Step 5: Execute migration
            self.logger.info("Step 3: Executing migration...")
            
            if config.get('dry_run', False):
                return self._dry_run_migration(processing_items)
            
            batch_results = batch_processor.process_items(
                items=processing_items,
                processor_func=self._process_candidate,
                context={'config': config, 'checkpoint': checkpoint}
            )
            
            # Step 6: Update checkpoint and generate results
            checkpoint.mark_completed()
            
            # Compile results
            results = {
                'success': True,
                'migration_id': self.migration_id,
                'statistics': self.stats,
                'processing_summary': batch_processor.get_processing_summary(),
                'progress_info': progress_tracker.get_summary(),
                'failed_items': [item.data for item in batch_processor.get_failed_items()],
                'checkpoint_id': checkpoint.id
            }
            
            self.logger.info(f"Migration completed successfully. Created {self.stats['processes_created']} processes")
            return results
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'statistics': self.stats
            }
    
    def _process_candidate(self, item: ProcessingItem) -> Dict[str, Any]:
        """
        Process a single process candidate.
        
        Args:
            item: ProcessingItem containing candidate data
            
        Returns:
            Processing result
        """
        candidate_data = item.data
        
        try:
            with transaction.atomic():
                # Create or get department
                department = self._get_or_create_department(candidate_data['department_name'])
                
                # Create process
                process = Process.objects.create(
                    name=candidate_data['process_name'],
                    description=candidate_data['description'],
                    department=department,
                    region=candidate_data.get('region'),
                    section=candidate_data.get('section'),
                    created_by=candidate_data.get('created_by'),
                    is_active=True
                )
                
                self.stats['processes_created'] += 1
                
                # Create documents
                documents_created = 0
                for file_data in candidate_data['files']:
                    if file_data['document_type']:
                        document = self._create_process_document(process, file_data)
                        if document:
                            documents_created += 1
                
                self.stats['documents_created'] += documents_created
                
                # Log successful migration
                self.logger.info(f"Migrated process: {process.name} with {documents_created} documents")
                
                return {
                    'process_id': process.id,
                    'documents_created': documents_created,
                    'success': True
                }
                
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing candidate {candidate_data['process_name']}: {e}")
            raise
    
    def _get_or_create_department(self, department_name: str) -> ProcessDepartment:
        """Get or create a process department."""
        department, created = ProcessDepartment.objects.get_or_create(
            name=department_name,
            defaults={
                'description': f'Department migrated from Knowledge Center',
                'order': ProcessDepartment.objects.count()
            }
        )
        
        if created:
            self.stats['departments_created'] += 1
            self.logger.info(f"Created department: {department_name}")
        
        return department
    
    def _create_process_document(self, process: Process, file_data: Dict) -> Optional[ProcessDocument]:
        """
        Create a ProcessDocument from file data.
        
        Args:
            process: Process instance
            file_data: Dictionary containing file information
            
        Returns:
            Created ProcessDocument or None if failed
        """
        try:
            # Check if document of this type already exists
            existing = ProcessDocument.objects.filter(
                process=process,
                document_type=file_data['document_type'],
                is_current=True
            ).first()
            
            if existing:
                # Mark existing as not current
                existing.is_current = False
                existing.save()
            
            # Create new document
            document = ProcessDocument.objects.create(
                process=process,
                document_type=file_data['document_type'],
                filename=file_data['filename'],
                original_filename=file_data['filename'],
                file_path=file_data['file_path'],
                original_file_path=file_data['file_path'],
                file_size=file_data.get('file_size', 0),
                version='1.0',
                is_current=True,
                uploaded_by=file_data.get('created_by'),
                metadata={
                    'migrated_from_kc': True,
                    'original_kc_file_id': file_data['id'],
                    'migration_date': timezone.now().isoformat()
                }
            )
            
            # Copy file if it exists and is accessible
            self._copy_file_to_process_storage(document, file_data)
            
            return document
            
        except Exception as e:
            self.logger.error(f"Error creating document {file_data['filename']}: {e}")
            return None
    
    def _copy_file_to_process_storage(self, document: ProcessDocument, file_data: Dict):
        """
        Copy file from KC storage to process management storage.
        
        Args:
            document: ProcessDocument instance
            file_data: File data dictionary
        """
        try:
            original_file = file_data.get('original_file')
            if original_file and original_file.file:
                # Generate new file path for process management
                new_filename = f"{document.process.id}_{document.document_type}_{document.filename}"
                new_path = f"uploads/processes/{new_filename}"
                
                # Copy file content
                with original_file.file.open('rb') as source:
                    document.file.save(new_filename, File(source), save=True)
                
                self.logger.debug(f"Copied file {document.filename} to process storage")
                
        except Exception as e:
            self.logger.warning(f"Could not copy file {document.filename}: {e}")
            # Document is still created, just without the file copy
    
    def _dry_run_migration(self, processing_items: List[ProcessingItem]) -> Dict[str, Any]:
        """
        Perform a dry run of the migration without making changes.
        
        Args:
            processing_items: List of items to process
            
        Returns:
            Dry run results
        """
        self.logger.info("Performing dry run migration...")
        
        dry_run_stats = {
            'total_candidates': len(processing_items),
            'departments_to_create': set(),
            'processes_to_create': 0,
            'documents_to_create': 0,
            'potential_issues': []
        }
        
        for item in processing_items:
            candidate_data = item.data
            
            # Check department
            dept_name = candidate_data['department_name']
            if not ProcessDepartment.objects.filter(name=dept_name).exists():
                dry_run_stats['departments_to_create'].add(dept_name)
            
            # Count processes and documents
            dry_run_stats['processes_to_create'] += 1
            dry_run_stats['documents_to_create'] += len([
                f for f in candidate_data['files'] if f['document_type']
            ])
            
            # Check for potential issues
            if not candidate_data['files']:
                dry_run_stats['potential_issues'].append(
                    f"Process '{candidate_data['process_name']}' has no files"
                )
            
            if len(candidate_data['process_name']) < 3:
                dry_run_stats['potential_issues'].append(
                    f"Process name too short: '{candidate_data['process_name']}'"
                )
        
        dry_run_stats['departments_to_create'] = list(dry_run_stats['departments_to_create'])
        
        self.logger.info(f"Dry run completed. Would create {dry_run_stats['processes_to_create']} processes")
        
        return {
            'success': True,
            'dry_run': True,
            'statistics': dry_run_stats
        }
    
    def get_migration_status(self, migration_id: str) -> Dict[str, Any]:
        """
        Get the status of a migration.
        
        Args:
            migration_id: Migration identifier
            
        Returns:
            Migration status information
        """
        try:
            from .models import MigrationCheckpoint
            
            checkpoint = MigrationCheckpoint.objects.filter(
                migration_id=migration_id
            ).first()
            
            if not checkpoint:
                return {'error': 'Migration not found'}
            
            return {
                'migration_id': migration_id,
                'status': checkpoint.get_status_display(),
                'progress_percentage': checkpoint.get_progress_percentage(),
                'success_rate': checkpoint.get_success_rate(),
                'total_items': checkpoint.total_items,
                'processed_items': checkpoint.processed_items,
                'successful_items': checkpoint.successful_items,
                'failed_items': checkpoint.failed_items,
                'started_at': checkpoint.started_at,
                'completed_at': checkpoint.completed_at,
                'can_resume': checkpoint.can_resume()
            }
            
        except Exception as e:
            return {'error': str(e)}