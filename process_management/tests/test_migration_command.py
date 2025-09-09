"""
Integration tests for the migration management command.
"""
import json
import tempfile
from io import StringIO
from django.test import TestCase, TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from unittest.mock import patch, MagicMock

from process_management.models import ProcessDepartment, Process, ProcessDocument
from process_management.management.commands.migrate_processes import Command
from process_management.services import FolderAnalysisService, DocumentCategorizationService
from knowledge_center.models import FolderApplication, KnowledgeCentreFolder, KnowldgeCentreFile
from it.users.models import Regions, Sections


class MigrateProcessesCommandTest(TransactionTestCase):
    """Test the migrate_processes management command."""
    
    def setUp(self):
        """Set up test data."""
        self.command = Command()
        self.out = StringIO()
        self.err = StringIO()
        
        # Create test regions and sections
        self.region = Regions.objects.create(region='Test Region')
        self.section = Sections.objects.create(section='Test Section', region=self.region)
        
        # Create test folder application
        self.processes_app = FolderApplication.objects.create(
            id=2,
            name='Processes and Procedures',
            description='Test processes app'
        )
    
    def test_command_help(self):
        """Test command help output."""
        with self.assertRaises(SystemExit):
            call_command('migrate_processes', '--help')
    
    def test_validate_migration_success(self):
        """Test successful migration validation."""
        result = self.command._validate_migration()
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_migration_with_existing_processes(self):
        """Test validation fails when processes already exist."""
        # Create a test department and process
        dept = ProcessDepartment.objects.create(
            name='TEST DEPARTMENT',
            description='Test department'
        )
        Process.objects.create(
            name='Test Process',
            department=dept
        )
        
        result = self.command._validate_migration()
        
        self.assertFalse(result['valid'])
        self.assertIn('Processes already exist', str(result['errors']))
    
    def test_create_departments_dry_run(self):
        """Test department creation in dry run mode."""
        initial_count = ProcessDepartment.objects.count()
        
        self.command._create_departments(dry_run=True)
        
        # No departments should be created in dry run
        self.assertEqual(ProcessDepartment.objects.count(), initial_count)
        self.assertEqual(self.command.migration_report['departments_created'], 11)
    
    def test_create_departments_actual(self):
        """Test actual department creation."""
        initial_count = ProcessDepartment.objects.count()
        
        self.command._create_departments(dry_run=False)
        
        # All 11 departments should be created
        self.assertEqual(ProcessDepartment.objects.count(), initial_count + 11)
        self.assertEqual(self.command.migration_report['departments_created'], 11)
        
        # Verify specific departments exist
        self.assertTrue(
            ProcessDepartment.objects.filter(name="GENERAL MANAGER'S OFFICE").exists()
        )
        self.assertTrue(
            ProcessDepartment.objects.filter(name="FINANCE").exists()
        )
    
    def test_extract_process_name(self):
        """Test process name extraction from filenames."""
        test_cases = [
            ('process_financial_approval.pdf', 'Financial Approval'),
            ('proc_maintenance_schedule.docx', 'Maintenance Schedule'),
            ('safety_procedure_manual.pdf', 'Safety Procedure Manual'),
            ('risk_assessment_map.xlsx', 'Risk Assessment'),
            ('', 'Unnamed Process'),
            ('simple_name', 'Simple Name'),
        ]
        
        for filename, expected in test_cases:
            result = self.command._extract_process_name(filename)
            self.assertEqual(result, expected, f"Failed for filename: {filename}")
    
    @patch('process_management.management.commands.migrate_processes.FolderAnalysisService')
    def test_dry_run_migration(self, mock_folder_service):
        """Test dry run migration execution."""
        # Mock analysis results
        mock_analysis = {
            'total_processes': 5,
            'processes_by_department': {
                'FINANCE': [
                    {'filename': 'budget_process.pdf', 'source': 'test'}
                ],
                'COMMERCIAL': [
                    {'filename': 'sales_process.pdf', 'source': 'test'}
                ]
            },
            'unmapped_processes': []
        }
        
        mock_folder_service.return_value.analyze_existing_processes.return_value = mock_analysis
        
        # Execute dry run
        call_command('migrate_processes', '--dry-run', stdout=self.out, stderr=self.err)
        
        output = self.out.getvalue()
        self.assertIn('DRY RUN MODE', output)
        self.assertIn('Dry run completed', output)
        
        # No actual objects should be created
        self.assertEqual(ProcessDepartment.objects.count(), 0)
        self.assertEqual(Process.objects.count(), 0)
    
    def test_rollback_functionality(self):
        """Test migration rollback functionality."""
        # Create some test data to rollback
        dept = ProcessDepartment.objects.create(
            name='TEST DEPARTMENT',
            description='Test department'
        )
        process = Process.objects.create(
            name='Test Process',
            department=dept
        )
        
        # Set up rollback info
        rollback_info = {
            'timestamp': '2024-01-01T00:00:00Z',
            'created_objects': {
                'departments': [dept.id],
                'processes': [process.id],
                'documents': []
            }
        }
        
        # Execute rollback
        self.command._rollback_migration(rollback_info)
        
        # Objects should be deleted
        self.assertFalse(ProcessDepartment.objects.filter(id=dept.id).exists())
        self.assertFalse(Process.objects.filter(id=process.id).exists())
    
    def test_migration_report_generation(self):
        """Test migration report generation."""
        # Set up some report data
        self.command.migration_report.update({
            'start_time': '2024-01-01T00:00:00Z',
            'end_time': '2024-01-01T01:00:00Z',
            'total_processes_created': 10,
            'total_documents_migrated': 25,
            'departments_created': 11,
            'errors': ['Test error'],
            'warnings': ['Test warning'],
        })
        
        # Generate report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        self.command._generate_migration_report(temp_file)
        
        # Verify report file was created
        with open(temp_file, 'r') as f:
            report_data = json.load(f)
        
        self.assertEqual(report_data['total_processes_created'], 10)
        self.assertEqual(report_data['total_documents_migrated'], 25)
        self.assertEqual(len(report_data['errors']), 1)
    
    def test_command_with_force_flag(self):
        """Test command execution with force flag."""
        # Create existing process to trigger validation error
        dept = ProcessDepartment.objects.create(
            name='TEST DEPARTMENT',
            description='Test department'
        )
        Process.objects.create(
            name='Existing Process',
            department=dept
        )
        
        # Mock the analysis service
        with patch('process_management.management.commands.migrate_processes.FolderAnalysisService') as mock_service:
            mock_analysis = {
                'total_processes': 0,
                'processes_by_department': {},
                'unmapped_processes': []
            }
            mock_service.return_value.analyze_existing_processes.return_value = mock_analysis
            
            # Should succeed with --force flag
            call_command('migrate_processes', '--force', '--dry-run', stdout=self.out)
            
            output = self.out.getvalue()
            self.assertIn('Migration completed', output)
    
    def test_command_validation_only(self):
        """Test command with validation-only flag."""
        call_command('migrate_processes', '--validate-only', stdout=self.out)
        
        output = self.out.getvalue()
        self.assertIn('VALIDATION RESULTS', output)
        self.assertIn('Migration validation passed', output)
    
    def test_command_report_only(self):
        """Test command with report-only flag."""
        with patch('process_management.management.commands.migrate_processes.FolderAnalysisService') as mock_service:
            mock_analysis = {
                'total_processes': 3,
                'processes_by_department': {
                    'FINANCE': [{'filename': 'test.pdf'}]
                },
                'unmapped_processes': []
            }
            mock_service.return_value.analyze_existing_processes.return_value = mock_analysis
            mock_service.return_value.get_analysis_report.return_value = {
                'folders_analyzed': 5,
                'processes_identified': 3,
                'mapping_errors': []
            }
            
            call_command('migrate_processes', '--report-only', stdout=self.out)
            
            output = self.out.getvalue()
            self.assertIn('ANALYSIS REPORT', output)
            self.assertIn('Total processes found: 3', output)
    
    def test_progress_tracking(self):
        """Test progress tracking functionality."""
        self.command.progress_callback = self.command._show_progress
        
        # Capture output
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.command._show_progress('Test message', 50, 100)
            output = fake_out.getvalue()
            self.assertIn('[50.0%] Test message', output)
    
    def test_error_handling_and_rollback(self):
        """Test error handling and automatic rollback."""
        with patch('process_management.management.commands.migrate_processes.FolderAnalysisService') as mock_service:
            # Make the service raise an exception
            mock_service.return_value.analyze_existing_processes.side_effect = Exception('Test error')
            
            with self.assertRaises(CommandError):
                call_command('migrate_processes', stdout=self.out, stderr=self.err)
            
            error_output = self.err.getvalue()
            self.assertIn('Migration failed', error_output)


class MigrationServicesIntegrationTest(TestCase):
    """Integration tests for migration services."""
    
    def setUp(self):
        """Set up test data."""
        self.folder_service = FolderAnalysisService()
        self.doc_service = DocumentCategorizationService()
        
        # Create test folder application
        self.processes_app = FolderApplication.objects.create(
            id=2,
            name='Processes and Procedures',
            description='Test processes app'
        )
    
    def test_folder_analysis_service_integration(self):
        """Test folder analysis service with real data."""
        # Create test folder structure
        root_folder = KnowledgeCentreFolder.objects.create(
            name='Finance',
            folder_application=self.processes_app
        )
        
        # Create test file
        test_file = KnowldgeCentreFile.objects.create(
            filename='budget_process.pdf',
            folder=root_folder,
            archived=False
        )
        
        # Analyze
        result = self.folder_service.analyze_existing_processes()
        
        self.assertGreater(result['total_processes'], 0)
        self.assertIn('FINANCE', result['processes_by_department'])
    
    def test_document_categorization_integration(self):
        """Test document categorization with various file types."""
        test_files = [
            ('budget_approval_process_map.pdf', 'process_map'),
            ('financial_procedure_manual.docx', 'procedure'),
            ('risk_register_finance.xlsx', 'risk_register'),
            ('unknown_document.txt', None),
        ]
        
        for filename, expected_type in test_files:
            doc_type, confidence = self.doc_service.categorize_document(filename)
            
            if expected_type:
                self.assertEqual(doc_type, expected_type, f"Failed for {filename}")
                self.assertGreater(confidence, 0.25)
            else:
                self.assertIsNone(doc_type, f"Should not categorize {filename}")
    
    def test_end_to_end_migration_flow(self):
        """Test complete migration flow from analysis to creation."""
        # Create test data
        root_folder = KnowledgeCentreFolder.objects.create(
            name='Commercial',
            folder_application=self.processes_app
        )
        
        test_file = KnowldgeCentreFile.objects.create(
            filename='sales_process_map.pdf',
            folder=root_folder,
            archived=False
        )
        
        # Run analysis
        analysis_result = self.folder_service.analyze_existing_processes()
        
        # Verify analysis found our test data
        self.assertIn('COMMERCIAL', analysis_result['processes_by_department'])
        
        # Test document categorization
        for dept_processes in analysis_result['processes_by_department'].values():
            for process_data in dept_processes:
                doc_type, confidence = self.doc_service.categorize_document(
                    process_data['filename']
                )
                if doc_type:
                    self.assertIn(doc_type, ['process_map', 'procedure', 'risk_register'])
                    self.assertGreater(confidence, 0.0)