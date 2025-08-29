"""
Enhanced Django management command to migrate existing folder-based processes to the new relational structure.

This command implements improved architecture with:
- Batch processing with configurable batch sizes
- Comprehensive error handling that continues processing on individual failures
- Enhanced progress tracking and reporting
- Idempotent migration with resume capability
- Backward compatibility with existing command-line options
"""
import os
import json
import traceback
import time
from typing import Dict, List, Optional, Tuple, Any
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.conf import settings
from django.utils import timezone

from process_management.models import ProcessDepartment, Process, ProcessDocument
from process_management.services import FolderAnalysisService, DocumentCategorizationService
from process_management.migration_infrastructure import (
    BatchProcessor, ErrorRecoveryManager, ProgressTracker, 
    ProcessingItem, ProcessingStatus, ErrorType,
    CheckpointManager, IdempotentMigrationManager
)
from process_management.process_creation_strategy import ProcessCreationStrategy
from knowledge_center.models import (
    FolderApplication, KnowledgeCentreFolder, KnowldgeCentreFile, 
    KnowledgeCenter
)
from it.users.models import Regions, Sections, UserProfile


class Command(BaseCommand):
    help = 'Migrate existing folder-based processes to the new relational structure with enhanced error handling'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder_service = FolderAnalysisService()
        self.doc_service = DocumentCategorizationService()
        self.process_strategy = ProcessCreationStrategy()
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
            'batch_summary': {},
            'performance_metrics': {},
        }
        self.created_objects = {
            'departments': [],
            'processes': [],
            'documents': [],
        }
        
        # Enhanced infrastructure components
        self.progress_tracker: Optional[ProgressTracker] = None
        self.error_manager: Optional[ErrorRecoveryManager] = None
        self.batch_processor: Optional[BatchProcessor] = None
        self.checkpoint_manager: Optional[CheckpointManager] = None
        self.idempotent_manager: Optional[IdempotentMigrationManager] = None

    def add_arguments(self, parser):
        # Existing arguments for backward compatibility
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
        
        # New enhanced arguments
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of items to process in each batch (default: 50)',
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retry attempts for failed items (default: 3)',
        )
        parser.add_argument(
            '--resume',
            action='store_true',
            help='Resume migration from last checkpoint',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip items that have already been migrated',
        )
        parser.add_argument(
            '--error-threshold',
            type=float,
            default=0.1,
            help='Stop migration if error rate exceeds this threshold (default: 0.1)',
        )

    def handle(self, *args, **options):
        """Main command handler with enhanced error handling and batch processing."""
        self.migration_report['start_time'] = timezone.now()
        
        # Initialize enhanced infrastructure
        self.error_manager = ErrorRecoveryManager(
            max_retries=options['max_retries'],
            base_delay=1.0,
            max_delay=60.0
        )
        
        try:
            # Handle rollback request
            if options['rollback']:
                return self._handle_rollback()
            
            # Handle resume request
            if options['resume']:
                return self._handle_resume_migration(options)
            
            self.stdout.write(
                self.style.SUCCESS('Starting enhanced process migration...')
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
            
            # Step 2: Analyze existing data with enhanced analysis
            self.stdout.write('Step 2: Analyzing existing processes with enhanced logic...')
            analysis_result = self._analyze_knowledge_center_structure()
            
            self.stdout.write(
                f'Found {analysis_result["total_documents"]} documents to process into logical processes'
            )
            
            if options['report_only']:
                self._generate_analysis_report(analysis_result)
                return
            
            # Step 3: Initialize progress tracking
            total_items = analysis_result.get('total_documents', 0)
            if options['progress'] and total_items > 0:
                self.progress_tracker = ProgressTracker(
                    total_items=total_items,
                    description="Migrating processes"
                )
                self.progress_tracker.set_progress_callback(self._display_progress)
            
            # Step 4: Initialize batch processor
            self.batch_processor = BatchProcessor(
                batch_size=options['batch_size'],
                progress_tracker=self.progress_tracker,
                error_manager=self.error_manager
            )
            
            # Step 5: Initialize idempotent migration manager
            self.idempotent_manager = IdempotentMigrationManager(
                batch_size=options['batch_size']
            )
            
            # Step 6: Execute migration with enhanced architecture
            if options['dry_run']:
                self._execute_dry_run_migration(analysis_result, options)
            else:
                self._execute_idempotent_migration(analysis_result, options)
            
            # Step 6: Generate comprehensive report
            self.migration_report['end_time'] = timezone.now()
            self._generate_migration_report(options.get('output_file'))
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS('Enhanced dry run completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Enhanced migration completed successfully!')
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

    def _analyze_knowledge_center_structure(self) -> Dict:
        """
        Analyze knowledge center structure with enhanced logic to create logical processes.
        
        Returns:
            Dict containing enhanced analysis results
        """
        analysis_result = {
            'total_documents': 0,
            'documents_by_department': {},
            'business_functions': [],
            'process_candidates': [],
            'unmapped_documents': [],
            'department_consolidation': {},
        }
        
        try:
            # Get all knowledge center documents
            documents = self._collect_all_documents()
            analysis_result['total_documents'] = len(documents)
            
            if not documents:
                self.migration_report['warnings'].append('No documents found in knowledge center')
                return analysis_result
            
            # Consolidate department folders
            folders = KnowledgeCentreFolder.objects.filter(
                folder_application__id=2,  # Processes and procedures
                parent__isnull=True
            )
            
            department_consolidation = self.folder_service.consolidate_department_folders(list(folders))
            analysis_result['department_consolidation'] = {
                dept: [f.name for f in folders] for dept, folders in department_consolidation.items()
            }
            
            # Group documents by department
            for doc in documents:
                dept = doc.get('department', 'UNMAPPED')
                if dept not in analysis_result['documents_by_department']:
                    analysis_result['documents_by_department'][dept] = []
                analysis_result['documents_by_department'][dept].append(doc)
            
            # Analyze business functions from documents
            business_functions = self.process_strategy.analyze_business_functions(documents)
            analysis_result['business_functions'] = [
                {
                    'name': bf.name,
                    'department': bf.department,
                    'document_count': len(bf.documents),
                    'confidence': bf.confidence,
                    'document_types': bf.document_types
                }
                for bf in business_functions
            ]
            
            # Create process candidates
            process_candidates = self.process_strategy.create_process_candidates(business_functions)
            analysis_result['process_candidates'] = [
                {
                    'name': pc.name,
                    'process_code': pc.process_code,
                    'department': pc.department,
                    'document_count': len(pc.documents),
                    'confidence': pc.confidence,
                    'duplicate_handling_applied': pc.duplicate_handling_applied
                }
                for pc in process_candidates
            ]
            
        except Exception as e:
            error_msg = f'Error in enhanced analysis: {str(e)}'
            self.migration_report['errors'].append(error_msg)
            self.stdout.write(self.style.ERROR(error_msg))
        
        return analysis_result

    def _collect_all_documents(self) -> List[Dict]:
        """
        Collect all documents from knowledge center with enhanced metadata and file system checks.
        
        Returns:
            List of document dictionaries with enhanced metadata
        """
        from process_management.file_system_handler import FileSystemAccessibilityChecker
        
        documents = []
        fs_checker = FileSystemAccessibilityChecker()
        
        try:
            # Get documents from KnowledgeCentreFolder structure
            folders = KnowledgeCentreFolder.objects.filter(
                folder_application__id=2  # Processes and procedures
            )
            
            for folder in folders:
                folder_files = KnowldgeCentreFile.objects.filter(folder=folder)
                dept_name = self.folder_service._map_folder_to_department_with_fuzzy(folder.name)
                
                for file_obj in folder_files:
                    # Perform file system accessibility check
                    file_path = str(file_obj.file) if file_obj.file else file_obj.filename
                    fs_check_result = fs_checker.check_file_accessibility(file_path)
                    
                    doc_info = {
                        'id': f'folder_{file_obj.id}',
                        'filename': file_obj.filename,
                        'file_path': file_path,
                        'folder_path': self._get_folder_path(folder),
                        'department': dept_name or 'UNMAPPED',
                        'file_size': fs_check_result.file_size or getattr(file_obj, 'file_size', 0),
                        'created_date': getattr(file_obj, 'created_date', None),
                        'source': 'knowledge_center_folder',
                        'folder_id': folder.id,
                        'file_id': file_obj.id,
                        'content_hint': self._extract_content_hints(file_obj.filename, folder.name),
                        'file_system_check': {
                            'status': fs_check_result.status.value,
                            'is_accessible': fs_check_result.status.value == 'accessible',
                            'error_type': fs_check_result.error_type.value if fs_check_result.error_type else None,
                            'error_message': fs_check_result.error_message,
                            'sanitized_path': fs_check_result.sanitized_path,
                            'is_readable': fs_check_result.is_readable,
                            'mime_type': fs_check_result.mime_type
                        }
                    }
                    documents.append(doc_info)
            
            # Get documents from legacy KnowledgeCenter
            legacy_docs = KnowledgeCenter.objects.filter(archived=False)
            
            for doc in legacy_docs:
                dept_name = self.folder_service._map_folder_to_department_with_fuzzy(
                    doc.sub_category_1 or ''
                )
                
                # Perform file system accessibility check for legacy documents
                file_path = doc.filepath if hasattr(doc, 'filepath') and doc.filepath else doc.filename
                fs_check_result = fs_checker.check_file_accessibility(file_path)
                
                doc_info = {
                    'id': f'legacy_{doc.id}',
                    'filename': doc.filename,
                    'file_path': file_path,
                    'folder_path': doc.sub_category_1 or '',
                    'department': dept_name or 'UNMAPPED',
                    'file_size': fs_check_result.file_size or 0,
                    'created_date': getattr(doc, 'created_date', None),
                    'source': 'legacy_knowledge_center',
                    'legacy_id': doc.id,
                    'section': doc.section,
                    'region': doc.region,
                    'file_type': doc.file_type,
                    'content_hint': self._extract_content_hints(doc.filename, doc.sub_category_1 or ''),
                    'file_system_check': {
                        'status': fs_check_result.status.value,
                        'is_accessible': fs_check_result.status.value == 'accessible',
                        'error_type': fs_check_result.error_type.value if fs_check_result.error_type else None,
                        'error_message': fs_check_result.error_message,
                        'sanitized_path': fs_check_result.sanitized_path,
                        'is_readable': fs_check_result.is_readable,
                        'mime_type': fs_check_result.mime_type
                    }
                }
                documents.append(doc_info)
                
        except Exception as e:
            error_msg = f'Error collecting documents: {str(e)}'
            self.migration_report['errors'].append(error_msg)
        
        return documents

    def _get_folder_path(self, folder: KnowledgeCentreFolder) -> str:
        """Get the full path of a folder including parent folders."""
        path_parts = [folder.name]
        current_folder = folder
        
        while current_folder.parent:
            current_folder = current_folder.parent
            path_parts.insert(0, current_folder.name)
        
        return '/'.join(path_parts)

    def _extract_content_hints(self, filename: str, folder_name: str) -> str:
        """Extract content hints from filename and folder context."""
        hints = []
        
        # Extract hints from filename
        filename_lower = filename.lower()
        if 'process' in filename_lower:
            hints.append('process')
        if 'procedure' in filename_lower:
            hints.append('procedure')
        if 'manual' in filename_lower:
            hints.append('manual')
        if 'risk' in filename_lower:
            hints.append('risk')
        if 'safety' in filename_lower:
            hints.append('safety')
        
        # Extract hints from folder context
        folder_lower = folder_name.lower()
        if 'maintenance' in folder_lower:
            hints.append('maintenance')
        if 'finance' in folder_lower:
            hints.append('finance')
        if 'hr' in folder_lower:
            hints.append('human_resources')
        
        return ' '.join(hints)

    def _execute_enhanced_migration(self, analysis_result: Dict, options: Dict):
        """
        Execute migration with enhanced batch processing and error handling.
        
        Args:
            analysis_result: Results from knowledge center analysis
            options: Command line options
        """
        self.stdout.write(self.style.SUCCESS('\n=== ENHANCED MIGRATION MODE ==='))
        
        try:
            # Step 1: Create departments
            self.stdout.write('Creating departments with enhanced logic...')
            self._create_departments_enhanced(dry_run=False)
            
            # Step 2: Create processing items from process candidates
            processing_items = self._create_processing_items(analysis_result)
            
            if not processing_items:
                self.stdout.write(self.style.WARNING('No processing items created'))
                return
            
            # Step 3: Process items in batches with enhanced error handling
            self.stdout.write(f'Processing {len(processing_items)} items in batches of {options["batch_size"]}...')
            
            batch_results = self.batch_processor.process_items(
                processing_items,
                self._process_single_item,
                context={'options': options}
            )
            
            # Step 4: Handle any retry items
            retry_items = self.batch_processor.get_retry_items()
            if retry_items:
                self.stdout.write(f'Retrying {len(retry_items)} failed items...')
                retry_results = self.batch_processor.process_items(
                    retry_items,
                    self._process_single_item,
                    context={'options': options, 'is_retry': True}
                )
                batch_results.extend(retry_results)
            
            # Step 5: Update migration report with batch results
            self._update_report_with_batch_results(batch_results)
            
            # Step 6: Check error threshold
            error_rate = self._calculate_error_rate(batch_results)
            if error_rate > options['error_threshold']:
                self.stdout.write(
                    self.style.ERROR(f'Error rate {error_rate:.2%} exceeds threshold {options["error_threshold"]:.2%}')
                )
                raise CommandError('Migration stopped due to high error rate')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Enhanced migration failed: {str(e)}'))
            raise

    def _create_processing_items(self, analysis_result: Dict) -> List[ProcessingItem]:
        """
        Create processing items from analysis results.
        
        Args:
            analysis_result: Results from knowledge center analysis
            
        Returns:
            List of ProcessingItem instances
        """
        processing_items = []
        
        # Create items from process candidates
        for candidate_data in analysis_result.get('process_candidates', []):
            item = ProcessingItem(
                id=f"process_{candidate_data['name']}_{candidate_data['process_code']}",
                data={
                    'type': 'process_candidate',
                    'candidate_data': candidate_data,
                    'analysis_result': analysis_result
                }
            )
            processing_items.append(item)
        
        return processing_items

    def _process_single_item(self, item: ProcessingItem) -> Any:
        """
        Process a single item (process candidate) with enhanced error handling.
        
        Args:
            item: Processing item to handle
            
        Returns:
            Result of processing
        """
        try:
            if item.data['type'] == 'process_candidate':
                # Check if this process already exists (idempotency check)
                candidate_data = item.data['candidate_data']
                existing_process = self._check_process_already_exists(candidate_data)
                
                if existing_process:
                    self.stdout.write(f'Process already exists: {existing_process.name} ({existing_process.process_code})')
                    return existing_process
                
                return self._create_process_from_candidate(candidate_data)
            else:
                raise ValueError(f"Unknown item type: {item.data['type']}")
                
        except Exception as e:
            # Let the error manager handle this
            raise e

    def _check_process_already_exists(self, candidate_data: Dict) -> Optional[Process]:
        """
        Check if a process with the same code or name already exists.
        
        Args:
            candidate_data: Process candidate information
            
        Returns:
            Existing Process instance if found, None otherwise
        """
        process_code = candidate_data.get('process_code', '')
        process_name = candidate_data.get('name', '')
        department_name = candidate_data.get('department', '')
        
        # Check by process code first (most specific)
        if process_code:
            existing = Process.objects.filter(process_code=process_code).first()
            if existing:
                return existing
        
        # Check by name and department combination
        if process_name and department_name:
            try:
                department = ProcessDepartment.objects.get(name=department_name)
                existing = Process.objects.filter(
                    name=process_name,
                    department=department
                ).first()
                if existing:
                    return existing
            except ProcessDepartment.DoesNotExist:
                pass
        
        return None

    def _check_document_already_migrated(self, filename: str, folder_path: str) -> bool:
        """
        Check if a document has already been migrated based on filename and folder path.
        
        Args:
            filename: Original filename
            folder_path: Original folder path
            
        Returns:
            True if document has already been migrated
        """
        # Check if any ProcessDocument exists with similar filename
        # This is a simple check - could be enhanced with more sophisticated matching
        similar_docs = ProcessDocument.objects.filter(
            filename__icontains=filename.split('.')[0]  # Check base filename without extension
        )
        
        for doc in similar_docs:
            # Additional checks could be added here to verify it's the same document
            # For now, we'll use a simple filename match
            if doc.filename.lower() == filename.lower():
                return True
        
        return False

    def _get_migration_items_for_resume(self) -> List[ProcessingItem]:
        """
        Get processing items for resume functionality.
        
        Returns:
            List of ProcessingItem instances for items that need to be processed
        """
        if not self.checkpoint_manager:
            return []
        
        # Get pending migration items
        pending_items = self.checkpoint_manager.get_pending_items()
        
        # Convert to ProcessingItem instances
        processing_items = []
        for migration_item in pending_items:
            processing_item = ProcessingItem(
                id=migration_item.item_id,
                data=migration_item.item_data,
                status=ProcessingStatus.PENDING
            )
            processing_items.append(processing_item)
        
        return processing_items

    def _create_process_from_candidate(self, candidate_data: Dict) -> Process:
        """
        Create a process from candidate data and associate documents with file system error handling.
        
        Args:
            candidate_data: Process candidate information
            
        Returns:
            Created Process instance
        """
        from process_management.file_system_handler import FileSystemErrorHandler
        
        # Get department
        try:
            department = ProcessDepartment.objects.get(name=candidate_data['department'])
        except ProcessDepartment.DoesNotExist:
            raise ValueError(f"Department not found: {candidate_data['department']}")
        
        # Create process
        process = Process(
            name=candidate_data['name'],
            process_code=candidate_data['process_code'],
            department=department,
            description=f"Auto-created process from {candidate_data['document_count']} documents",
            is_active=True
        )
        
        # Validate and save
        process.full_clean()
        process.save()
        
        # Track created object for rollback
        self.created_objects['processes'].append(process.id)
        
        # Create associated documents with file system error handling
        if 'documents' in candidate_data:
            self._create_process_documents_with_fs_handling(process, candidate_data['documents'])
        
        return process
    
    def _create_process_documents_with_fs_handling(self, process: Process, documents: List[Dict]):
        """
        Create ProcessDocument instances with comprehensive file system error handling.
        
        Args:
            process: Process instance to associate documents with
            documents: List of document dictionaries
        """
        from process_management.file_system_handler import FileSystemErrorHandler
        
        fs_error_handler = FileSystemErrorHandler()
        created_documents = 0
        failed_documents = 0
        
        for doc_data in documents:
            try:
                # Extract file information
                filename = doc_data.get('filename', 'unknown_file')
                file_path = doc_data.get('file_path', doc_data.get('filepath', ''))
                
                # Check file system status from previous check or perform new check
                fs_check = doc_data.get('file_system_check', {})
                
                # Determine document status based on file system check
                document_status = self._determine_document_status(fs_check)
                
                # Categorize document type
                doc_type = self.doc_service.categorize_document(filename, doc_data.get('folder_path', ''))
                
                # Create ProcessDocument with appropriate status
                process_document = ProcessDocument(
                    process=process,
                    filename=filename,
                    original_filename=filename,
                    file_path=fs_check.get('sanitized_path', file_path) if fs_check.get('sanitized_path') else file_path,
                    original_file_path=file_path,
                    document_type=doc_type,
                    file_size=doc_data.get('file_size', 0),
                    mime_type=fs_check.get('mime_type', ''),
                    status=document_status,
                    is_active=document_status in ['accessible', 'sanitized'],
                    metadata={
                        'source': doc_data.get('source', 'unknown'),
                        'department': doc_data.get('department', ''),
                        'folder_path': doc_data.get('folder_path', ''),
                        'content_hint': doc_data.get('content_hint', ''),
                        'file_system_check': fs_check,
                        'migration_timestamp': timezone.now().isoformat()
                    }
                )
                
                # Handle file system errors if present
                if fs_check.get('error_type'):
                    error_result = fs_error_handler.handle_file_system_error(
                        file_path,
                        context={
                            'process_id': process.id,
                            'document_filename': filename,
                            'source': doc_data.get('source', 'unknown')
                        }
                    )
                    
                    # Update document metadata with error handling results
                    process_document.metadata['file_system_error'] = error_result
                    
                    # Log the error
                    error_msg = f"File system error for document '{filename}': {fs_check.get('error_message', 'Unknown error')}"
                    self.migration_report['errors'].append(error_msg)
                    self.stdout.write(self.style.WARNING(f"  Warning: {error_msg}"))
                
                # Validate and save document
                process_document.full_clean()
                process_document.save()
                
                # Track created document for rollback
                self.created_objects['documents'].append(process_document.id)
                created_documents += 1
                
                # Update migration report
                self.migration_report['total_documents_migrated'] += 1
                
            except Exception as e:
                failed_documents += 1
                error_msg = f"Failed to create document '{doc_data.get('filename', 'unknown')}' for process '{process.name}': {str(e)}"
                self.migration_report['errors'].append(error_msg)
                self.stdout.write(self.style.ERROR(f"  Error: {error_msg}"))
        
        self.stdout.write(f"  Created {created_documents} documents for process '{process.name}' ({failed_documents} failed)")
    
    def _determine_document_status(self, fs_check: Dict) -> str:
        """
        Determine document status based on file system check results.
        
        Args:
            fs_check: File system check results dictionary
            
        Returns:
            Document status string
        """
        status = fs_check.get('status', 'unknown')
        
        # Map file system status to document status
        status_mapping = {
            'accessible': 'accessible',
            'sanitized': 'sanitized',
            'missing': 'missing_file',
            'permission_denied': 'permission_denied',
            'corrupted': 'corrupted',
            'invalid_path': 'invalid_path',
            'inaccessible': 'inaccessible'
        }
        
        return status_mapping.get(status, 'error')

    def _create_departments_enhanced(self, dry_run: bool = False):
        """Create predefined process departments with enhanced logic."""
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
            ("SAFETY", "Safety", 12),
            ("UNMAPPED", "Unmapped Departments", 99),
        ]
        
        created_count = 0
        
        for name, description, order in departments:
            if not dry_run:
                try:
                    dept, created = ProcessDepartment.objects.get_or_create(
                        name=name,
                        defaults={
                            'description': description,
                            'order': order
                        }
                    )
                    if created:
                        created_count += 1
                        self.created_objects['departments'].append(dept.id)
                        self.stdout.write(f'  Created department: {name}')
                    else:
                        self.stdout.write(f'  Department already exists: {name}')
                except Exception as e:
                    error_msg = f'Error creating department {name}: {str(e)}'
                    self.migration_report['errors'].append(error_msg)
                    self.stdout.write(self.style.ERROR(f'  {error_msg}'))
            else:
                self.stdout.write(f'  [DRY RUN] Would create department: {name}')
                created_count += 1
        
        self.migration_report['departments_created'] = created_count

    def _update_report_with_batch_results(self, batch_results: List):
        """Update migration report with batch processing results."""
        total_successful = sum(len(batch.successful_items) for batch in batch_results)
        total_failed = sum(len(batch.failed_items) for batch in batch_results)
        total_skipped = sum(len(batch.skipped_items) for batch in batch_results)
        total_time = sum(batch.processing_time for batch in batch_results)
        
        self.migration_report['total_processes_created'] = total_successful
        self.migration_report['batch_summary'] = {
            'total_batches': len(batch_results),
            'successful_items': total_successful,
            'failed_items': total_failed,
            'skipped_items': total_skipped,
            'total_processing_time': total_time,
            'average_batch_time': total_time / len(batch_results) if batch_results else 0,
        }
        
        # Add error details from batch results
        for batch in batch_results:
            for failed_item in batch.failed_items:
                if failed_item.error_message:
                    self.migration_report['errors'].append(
                        f'Item {failed_item.id}: {failed_item.error_message}'
                    )

    def _calculate_error_rate(self, batch_results: List) -> float:
        """Calculate overall error rate from batch results."""
        total_items = sum(batch.total_items for batch in batch_results)
        total_failed = sum(len(batch.failed_items) for batch in batch_results)
        
        return total_failed / total_items if total_items > 0 else 0.0

    def _display_progress(self, progress_info: Dict):
        """Display progress information to stdout."""
        message = (f"Progress: {progress_info['percentage']:.1f}% "
                  f"({progress_info['processed_items']}/{progress_info['total_items']}) "
                  f"- Rate: {progress_info['rate_per_second']:.1f}/s")
        
        if progress_info['eta_seconds'] > 0:
            eta_minutes = int(progress_info['eta_seconds'] / 60)
            if eta_minutes > 0:
                message += f" - ETA: {eta_minutes}m"
            else:
                message += f" - ETA: {int(progress_info['eta_seconds'])}s"
        
        self.stdout.write(message)

    def _execute_dry_run_migration(self, analysis_result: Dict, options: Dict):
        """Execute migration in dry-run mode with enhanced reporting."""
        self.stdout.write(self.style.SUCCESS('\n=== ENHANCED DRY RUN MODE ==='))
        
        # Step 1: Create departments (dry run)
        self.stdout.write('Creating departments...')
        self._create_departments_enhanced(dry_run=True)
        
        # Step 2: Show what would be processed
        process_candidates = analysis_result.get('process_candidates', [])
        self.stdout.write(f'Would create {len(process_candidates)} processes:')
        
        for candidate in process_candidates[:10]:  # Show first 10
            self.stdout.write(f'  - {candidate["name"]} ({candidate["process_code"]}) '
                            f'in {candidate["department"]} with {candidate["document_count"]} documents')
        
        if len(process_candidates) > 10:
            self.stdout.write(f'  ... and {len(process_candidates) - 10} more processes')
        
        # Step 3: Show batch processing plan
        batch_count = (len(process_candidates) + options['batch_size'] - 1) // options['batch_size']
        self.stdout.write(f'Would process in {batch_count} batches of {options["batch_size"]} items each')
        
        # Step 4: Show department distribution
        dept_dist = {}
        for candidate in process_candidates:
            dept = candidate['department']
            dept_dist[dept] = dept_dist.get(dept, 0) + 1
        
        self.stdout.write('Department distribution:')
        for dept, count in sorted(dept_dist.items()):
            self.stdout.write(f'  {dept}: {count} processes')
        
        self.stdout.write(self.style.SUCCESS('Enhanced dry run completed - no changes made'))

    def _handle_resume_migration(self, options: Dict) -> None:
        """
        Handle resume migration request.
        
        Args:
            options: Command line options
        """
        self.stdout.write(self.style.SUCCESS('Attempting to resume previous migration...'))
        
        try:
            # Initialize idempotent migration manager
            self.idempotent_manager = IdempotentMigrationManager(
                batch_size=options['batch_size']
            )
            
            # Try to resume migration
            pending_items, checkpoint = self.idempotent_manager.resume_migration()
            
            if not checkpoint:
                self.stdout.write(self.style.WARNING('No resumable migration found'))
                return
            
            if not pending_items:
                self.stdout.write(self.style.SUCCESS('Migration already completed'))
                return
            
            # Display resume information
            summary = self.idempotent_manager.checkpoint_manager.get_checkpoint_summary()
            self.stdout.write(f'Resuming migration: {summary["migration_id"]}')
            self.stdout.write(f'Progress: {summary["processed_items"]}/{summary["total_items"]} '
                            f'({summary["progress_percentage"]:.1f}%)')
            self.stdout.write(f'Remaining items: {len(pending_items)}')
            
            # Set up progress tracking for resume
            if options['progress']:
                self.progress_tracker = ProgressTracker(
                    total_items=len(pending_items),
                    description="Resuming migration"
                )
                self.progress_tracker.set_progress_callback(self._display_progress)
            
            # Execute remaining items
            config = {
                'batch_size': options['batch_size'],
                'max_retries': options['max_retries'],
                'error_threshold': options['error_threshold'],
                'skip_existing': options['skip_existing'],
                'resume': True
            }
            
            results = self.idempotent_manager.execute_idempotent_migration(
                pending_items,
                self._process_single_item,
                config,
                skip_existing=False  # Don't skip since we already filtered
            )
            
            # Update migration report
            self._update_report_with_resume_results(results)
            
            # Generate final report
            self.migration_report['end_time'] = timezone.now()
            self._generate_migration_report(options.get('output_file'))
            
            self.stdout.write(self.style.SUCCESS('Migration resumed and completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Resume migration failed: {str(e)}'))
            raise CommandError(f'Resume migration failed: {str(e)}')

    def _execute_idempotent_migration(self, analysis_result: Dict, options: Dict):
        """
        Execute migration with idempotent behavior and checkpoint tracking.
        
        Args:
            analysis_result: Results from knowledge center analysis
            options: Command line options
        """
        self.stdout.write(self.style.SUCCESS('\n=== IDEMPOTENT MIGRATION MODE ==='))
        
        try:
            # Step 1: Create departments
            self.stdout.write('Creating departments with enhanced logic...')
            self._create_departments_enhanced(dry_run=False)
            
            # Step 2: Create processing items from process candidates
            processing_items = self._create_processing_items(analysis_result)
            
            if not processing_items:
                self.stdout.write(self.style.WARNING('No processing items created'))
                return
            
            # Step 3: Execute idempotent migration
            config = {
                'batch_size': options['batch_size'],
                'max_retries': options['max_retries'],
                'error_threshold': options['error_threshold'],
                'skip_existing': options['skip_existing'],
                'dry_run': options.get('dry_run', False),
                'force': options.get('force', False)
            }
            
            self.stdout.write(f'Processing {len(processing_items)} items with idempotent migration...')
            
            results = self.idempotent_manager.execute_idempotent_migration(
                processing_items,
                self._process_single_item,
                config,
                skip_existing=options['skip_existing']
            )
            
            # Step 4: Update migration report with results
            self._update_report_with_idempotent_results(results)
            
            # Step 5: Check error threshold
            batch_results = results.get('batch_results', {})
            total_items = batch_results.get('successful_items', 0) + batch_results.get('failed_items', 0)
            error_rate = batch_results.get('failed_items', 0) / max(total_items, 1)
            
            if error_rate > options['error_threshold']:
                self.stdout.write(
                    self.style.ERROR(f'Error rate {error_rate:.2%} exceeds threshold {options["error_threshold"]:.2%}')
                )
                raise CommandError('Migration stopped due to high error rate')
            
            # Display final summary
            self._display_migration_summary(results)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Idempotent migration failed: {str(e)}'))
            raise

    def _update_report_with_resume_results(self, results: Dict):
        """Update migration report with resume results."""
        checkpoint_summary = results.get('checkpoint_summary', {})
        batch_results = results.get('batch_results', {})
        
        self.migration_report['total_processes_created'] = checkpoint_summary.get('successful_items', 0)
        self.migration_report['resume_info'] = {
            'migration_id': checkpoint_summary.get('migration_id'),
            'resumed_from_checkpoint': True,
            'final_progress': checkpoint_summary.get('progress_percentage', 0),
            'success_rate': checkpoint_summary.get('success_rate', 0),
        }
        self.migration_report['batch_summary'] = batch_results

    def _update_report_with_idempotent_results(self, results: Dict):
        """Update migration report with idempotent migration results."""
        checkpoint_summary = results.get('checkpoint_summary', {})
        batch_results = results.get('batch_results', {})
        
        self.migration_report['total_processes_created'] = batch_results.get('successful_items', 0)
        self.migration_report['idempotent_info'] = {
            'migration_id': checkpoint_summary.get('migration_id'),
            'can_resume': results.get('can_resume', False),
            'final_progress': checkpoint_summary.get('progress_percentage', 0),
            'success_rate': checkpoint_summary.get('success_rate', 0),
        }
        self.migration_report['batch_summary'] = batch_results

    def _display_migration_summary(self, results: Dict):
        """Display comprehensive migration summary."""
        checkpoint_summary = results.get('checkpoint_summary', {})
        batch_results = results.get('batch_results', {})
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('MIGRATION SUMMARY'))
        self.stdout.write('='*60)
        
        self.stdout.write(f'Migration ID: {checkpoint_summary.get("migration_id", "N/A")}')
        self.stdout.write(f'Total Items: {checkpoint_summary.get("total_items", 0)}')
        self.stdout.write(f'Successful: {checkpoint_summary.get("successful_items", 0)}')
        self.stdout.write(f'Failed: {checkpoint_summary.get("failed_items", 0)}')
        self.stdout.write(f'Skipped: {checkpoint_summary.get("skipped_items", 0)}')
        self.stdout.write(f'Success Rate: {checkpoint_summary.get("success_rate", 0):.1f}%')
        
        if results.get('can_resume', False):
            self.stdout.write(self.style.WARNING('Migration can be resumed if needed'))
        else:
            self.stdout.write(self.style.SUCCESS('Migration completed successfully'))
        
        self.stdout.write('='*60)

    def _validate_migration(self) -> Dict:
        """Validate migration prerequisites with enhanced checks."""
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
                'Processes already exist. Use --force to override or --skip-existing to skip duplicates.'
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
        
        # Check knowledge center data availability
        try:
            folder_count = KnowledgeCentreFolder.objects.filter(
                folder_application__id=2
            ).count()
            legacy_count = KnowledgeCenter.objects.filter(archived=False).count()
            
            if folder_count == 0 and legacy_count == 0:
                validation_result['warnings'].append(
                    'No knowledge center data found to migrate'
                )
        except Exception as e:
            validation_result['errors'].append(
                f'Error checking knowledge center data: {str(e)}'
            )
        
        # Check enhanced infrastructure components
        try:
            # Test batch processor initialization
            test_processor = BatchProcessor(batch_size=1)
            test_error_manager = ErrorRecoveryManager()
            test_tracker = ProgressTracker(total_items=1)
        except Exception as e:
            validation_result['errors'].append(
                f'Enhanced infrastructure components not available: {str(e)}'
            )
            validation_result['valid'] = False
        
        self.migration_report['validation_results'] = validation_result
        return validation_result

    def _display_validation_results(self, validation_result: Dict):
        """Display validation results with enhanced formatting."""
        self.stdout.write(self.style.SUCCESS('\n=== ENHANCED VALIDATION RESULTS ==='))
        
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

    def _generate_analysis_report(self, analysis_result: Dict):
        """Generate and display enhanced analysis report."""
        self.stdout.write(self.style.SUCCESS('\n=== ENHANCED ANALYSIS REPORT ==='))
        
        # Basic statistics
        self.stdout.write(f'Total documents found: {analysis_result["total_documents"]}')
        self.stdout.write(f'Business functions identified: {len(analysis_result["business_functions"])}')
        self.stdout.write(f'Process candidates created: {len(analysis_result["process_candidates"])}')
        
        # Department consolidation results
        if analysis_result['department_consolidation']:
            self.stdout.write('\nDepartment consolidation:')
            for dept, folders in analysis_result['department_consolidation'].items():
                self.stdout.write(f'  {dept}: {len(folders)} folders ({", ".join(folders)})')
        
        # Business functions breakdown
        if analysis_result['business_functions']:
            self.stdout.write('\nBusiness functions identified:')
            for func in analysis_result['business_functions'][:10]:  # Show top 10
                self.stdout.write(f'  {func["name"]}: {func["document_count"]} docs '
                                f'(confidence: {func["confidence"]:.2f}) in {func["department"]}')
        
        # Process candidates breakdown
        if analysis_result['process_candidates']:
            self.stdout.write('\nTop process candidates:')
            for candidate in analysis_result['process_candidates'][:10]:  # Show top 10
                duplicate_note = " [DUPLICATE HANDLED]" if candidate['duplicate_handling_applied'] else ""
                self.stdout.write(f'  {candidate["name"]} ({candidate["process_code"]}): '
                                f'{candidate["document_count"]} docs{duplicate_note}')
        
        # Documents by department
        if analysis_result['documents_by_department']:
            self.stdout.write('\nDocuments by department:')
            for dept, docs in analysis_result['documents_by_department'].items():
                self.stdout.write(f'  {dept}: {len(docs)} documents')

    def _generate_migration_report(self, output_file: Optional[str] = None):
        """Generate comprehensive migration report with enhanced metrics."""
        duration = None
        if self.migration_report['start_time'] and self.migration_report['end_time']:
            duration = self.migration_report['end_time'] - self.migration_report['start_time']
        
        # Add performance metrics
        if self.batch_processor:
            processing_summary = self.batch_processor.get_processing_summary()
            self.migration_report['performance_metrics'] = processing_summary
        
        if self.error_manager:
            error_summary = self.error_manager.get_error_summary()
            self.migration_report['error_analysis'] = error_summary
        
        if self.progress_tracker:
            progress_summary = self.progress_tracker.get_summary()
            self.migration_report['progress_summary'] = progress_summary
        
        # Add process creation strategy report
        strategy_report = self.process_strategy.get_creation_report()
        self.migration_report['process_creation_analysis'] = strategy_report
        
        report = {
            **self.migration_report,
            'duration_seconds': duration.total_seconds() if duration else None,
            'folder_analysis': self.folder_service.get_analysis_report(),
            'document_analysis': self.doc_service.get_categorization_report(),
        }
        
        # Display enhanced summary
        self.stdout.write(self.style.SUCCESS('\n=== ENHANCED MIGRATION REPORT ==='))
        self.stdout.write(f'Duration: {duration}' if duration else 'Duration: Unknown')
        self.stdout.write(f'Departments created: {report["departments_created"]}')
        self.stdout.write(f'Processes created: {report["total_processes_created"]}')
        self.stdout.write(f'Documents analyzed: {report.get("process_creation_analysis", {}).get("documents_analyzed", 0)}')
        
        # Show batch processing summary
        if 'batch_summary' in report:
            batch_summary = report['batch_summary']
            self.stdout.write(f'Batches processed: {batch_summary["total_batches"]}')
            self.stdout.write(f'Average batch time: {batch_summary["average_batch_time"]:.2f}s')
        
        # Show performance metrics
        if 'performance_metrics' in report:
            perf = report['performance_metrics']
            self.stdout.write(f'Success rate: {perf.get("success_rate", 0):.1f}%')
            self.stdout.write(f'Processing rate: {perf.get("items_per_second", 0):.2f} items/sec')
        
        if report['errors']:
            self.stdout.write(self.style.ERROR(f'Errors: {len(report["errors"])}'))
            for error in report['errors'][:5]:  # Show first 5 errors
                self.stdout.write(f'  - {error}')
            if len(report['errors']) > 5:
                self.stdout.write(f'  ... and {len(report["errors"]) - 5} more errors')
        
        if report['warnings']:
            self.stdout.write(self.style.WARNING(f'Warnings: {len(report["warnings"])}'))
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                self.stdout.write(f'Enhanced report saved to: {output_file}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to save report: {str(e)}')
                )

    def _handle_rollback(self):
        """Handle rollback request with enhanced tracking."""
        self.stdout.write(self.style.WARNING('Starting enhanced rollback process...'))
        
        # Check if there's rollback information
        rollback_info = self.migration_report.get('rollback_info')
        if not rollback_info and self.created_objects:
            # Use tracked objects for rollback
            rollback_info = {'created_objects': self.created_objects}
        
        if not rollback_info:
            self.stdout.write(
                self.style.ERROR('No rollback information found. Cannot rollback.')
            )
            return
        
        try:
            self._rollback_migration(rollback_info)
            self.stdout.write(self.style.SUCCESS('Enhanced rollback completed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Rollback failed: {str(e)}'))
            raise CommandError(f'Rollback failed: {str(e)}')

    def _rollback_migration(self, rollback_info: Optional[Dict] = None):
        """Rollback migration changes with enhanced tracking."""
        if not rollback_info:
            rollback_info = self.migration_report.get('rollback_info', {})
        
        created_objects = rollback_info.get('created_objects', self.created_objects)
        
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
        
        # Clear tracking
        self.created_objects = {'departments': [], 'processes': [], 'documents': []}