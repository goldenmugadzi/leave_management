"""
Unit tests for migration services.
"""
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from process_management.services import FolderAnalysisService, DocumentCategorizationService
from process_management.models import ProcessDepartment, Process, ProcessDocument
from knowledge_center.models import (
    FolderApplication, KnowledgeCentreFolder, KnowldgeCentreFile, 
    KnowledgeCenter, Filetype, First_Category, Secondary_Category
)
from it.users.models import Regions, Sections, UserProfile


class FolderAnalysisServiceTest(TestCase):
    """Test cases for FolderAnalysisService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = FolderAnalysisService()
        
        # Create test departments
        self.dept_gm = ProcessDepartment.objects.create(
            name="GENERAL MANAGER'S OFFICE",
            description="GM Office",
            order=1
        )
        self.dept_finance = ProcessDepartment.objects.create(
            name="FINANCE",
            description="Finance Department",
            order=2
        )
        
        # Create test user
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        
        # Create test region and section
        self.region = Regions.objects.create(region='Test Region')
        self.section = Sections.objects.create(section='Test Section', code='TS')
    
    def test_department_mapping_direct_match(self):
        """Test direct department name mapping."""
        test_cases = [
            ('finance', 'FINANCE'),
            ('FINANCE', 'FINANCE'),
            ('commercial', 'COMMERCIAL'),
            ('hr', 'HUMAN RESOURCES AND ADMINISTRATION'),
            ('it', 'INFORMATION AND COMMUNICATION TECHNOLOGY'),
        ]
        
        for folder_name, expected_dept in test_cases:
            with self.subTest(folder_name=folder_name):
                result = self.service._map_folder_to_department(folder_name)
                self.assertEqual(result, expected_dept)
    
    def test_department_mapping_partial_match(self):
        """Test partial department name matching."""
        test_cases = [
            ('finance_department', 'FINANCE'),
            ('commercial_section', 'COMMERCIAL'),
            ('human_resources', 'HUMAN RESOURCES AND ADMINISTRATION'),
            ('information_technology', 'INFORMATION AND COMMUNICATION TECHNOLOGY'),
        ]
        
        for folder_name, expected_dept in test_cases:
            with self.subTest(folder_name=folder_name):
                result = self.service._map_folder_to_department(folder_name)
                self.assertEqual(result, expected_dept)
    
    def test_department_mapping_no_match(self):
        """Test department mapping with no match."""
        test_cases = ['unknown_dept', 'random_folder', '', None]
        
        for folder_name in test_cases:
            with self.subTest(folder_name=folder_name):
                result = self.service._map_folder_to_department(folder_name)
                self.assertIsNone(result)
    
    def test_department_mapping_pattern_based(self):
        """Test pattern-based department mapping."""
        test_cases = [
            ('general_manager_office', "GENERAL MANAGER'S OFFICE"),
            ('gm_office', "GENERAL MANAGER'S OFFICE"),
            ('engineering_manager', "ENGINEERING MANAGER'S OFFICE"),
            ('em_office', "ENGINEERING MANAGER'S OFFICE"),
        ]
        
        for folder_name, expected_dept in test_cases:
            with self.subTest(folder_name=folder_name):
                result = self.service._map_folder_to_department(folder_name)
                self.assertEqual(result, expected_dept)
    
    def test_identify_processes_from_folders(self):
        """Test process identification from folder structure."""
        folders = [
            'finance/budget_process',
            'hr/recruitment',
            'it/system_maintenance',
            '.git/hooks',  # Should be skipped
            '__pycache__/temp',  # Should be skipped
        ]
        
        processes = self.service._identify_processes_from_folders(folders)
        
        # Should identify 3 processes (skipping system folders)
        self.assertEqual(len(processes), 3)
        
        # Check process names
        process_names = [p['name'] for p in processes]
        self.assertIn('budget_process', process_names)
        self.assertIn('recruitment', process_names)
        self.assertIn('system_maintenance', process_names)
        
        # Check department mappings
        finance_process = next(p for p in processes if p['name'] == 'budget_process')
        self.assertEqual(finance_process['department'], 'FINANCE')
        
        hr_process = next(p for p in processes if p['name'] == 'recruitment')
        self.assertEqual(hr_process['department'], 'HUMAN RESOURCES AND ADMINISTRATION')
    
    def test_create_department_mapping(self):
        """Test creation of department to folder mapping."""
        folders = [
            'finance/budget',
            'finance/accounting',
            'hr/recruitment',
            'unknown/folder',
        ]
        
        mapping = self.service._create_department_mapping(folders)
        
        self.assertIn('FINANCE', mapping)
        self.assertIn('HUMAN RESOURCES AND ADMINISTRATION', mapping)
        self.assertNotIn('UNKNOWN', mapping)
        
        self.assertEqual(len(mapping['FINANCE']), 2)
        self.assertEqual(len(mapping['HUMAN RESOURCES AND ADMINISTRATION']), 1)
    
    def test_calculate_mapping_confidence(self):
        """Test confidence calculation for process-department mapping."""
        # High confidence - direct match
        confidence = self.service._calculate_mapping_confidence('finance_process', 'FINANCE')
        self.assertGreaterEqual(confidence, 0.7)
        
        # Medium confidence - partial match
        confidence = self.service._calculate_mapping_confidence('budget_management', 'FINANCE')
        self.assertGreaterEqual(confidence, 0.3)
        self.assertLess(confidence, 0.9)
        
        # Low confidence - no clear connection
        confidence = self.service._calculate_mapping_confidence('random_process', 'FINANCE')
        self.assertLessEqual(confidence, 0.5)
        
        # No confidence - no department
        confidence = self.service._calculate_mapping_confidence('process', None)
        self.assertEqual(confidence, 0.0)
    
    @patch('os.path.exists')
    @patch('os.walk')
    def test_analyze_folder_structure(self, mock_walk, mock_exists):
        """Test folder structure analysis."""
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('/test/uploads/processes', ['finance', 'hr'], ['root_file.pdf']),
            ('/test/uploads/processes/finance', [], ['budget.pdf', 'accounting.docx']),
            ('/test/uploads/processes/hr', [], ['recruitment.pdf']),
        ]
        
        with patch.object(self.service, '_get_file_size', return_value=1024):
            result = self.service.analyze_folder_structure('/test/uploads/processes')
        
        self.assertEqual(len(result['folders_found']), 2)
        self.assertIn('finance', result['folders_found'])
        self.assertIn('hr', result['folders_found'])
        
        self.assertEqual(len(result['files_found']), 4)
        
        # Check potential processes
        self.assertEqual(len(result['potential_processes']), 2)
        
        # Check department mapping
        self.assertIn('FINANCE', result['department_mapping'])
        self.assertIn('HUMAN RESOURCES AND ADMINISTRATION', result['department_mapping'])
    
    @patch('os.path.exists')
    def test_analyze_folder_structure_missing_path(self, mock_exists):
        """Test folder analysis with missing base path."""
        mock_exists.return_value = False
        
        result = self.service.analyze_folder_structure('/nonexistent/path')
        
        self.assertEqual(len(result['folders_found']), 0)
        self.assertEqual(len(result['files_found']), 0)
        self.assertIn('Base path does not exist', self.service.analysis_report['mapping_errors'][0])
    
    def test_analyze_existing_processes(self):
        """Test analysis of existing process data."""
        # Create test folder application for processes_and_procedures
        processes_app = FolderApplication.objects.create(
            id=2,
            name='processes_and_procedures'
        )
        
        # Create test folders
        finance_folder = KnowledgeCentreFolder.objects.create(
            name='Finance',
            folder_application=processes_app
        )
        
        hr_folder = KnowledgeCentreFolder.objects.create(
            name='Human Resources',
            folder_application=processes_app
        )
        
        # Create test files
        KnowldgeCentreFile.objects.create(
            filename='budget_process.pdf',
            name='Budget Process',
            folder=finance_folder,
            section=self.section,
            region=self.region,
            archived=False
        )
        
        KnowldgeCentreFile.objects.create(
            filename='hr_manual.pdf',
            name='HR Manual',
            folder=hr_folder,
            section=self.section,
            region=self.region,
            archived=False
        )
        
        # Create legacy knowledge center data
        filetype = Filetype.objects.create(name='Process')
        KnowledgeCenter.objects.create(
            filename='legacy_process.pdf',
            file_type='Process',
            sub_category_1='finance',
            filepath='/uploads/knowledge_center/legacy_process.pdf',
            archived=False
        )
        
        result = self.service.analyze_existing_processes()
        
        self.assertGreater(result['total_processes'], 0)
        self.assertIn('processes_by_department', result)
        self.assertIn('processes_by_folder', result)
    
    def test_get_analysis_report(self):
        """Test getting analysis report."""
        # Simulate some analysis
        self.service.analysis_report['folders_analyzed'] = 10
        self.service.analysis_report['processes_identified'] = 8
        self.service.analysis_report['mapping_errors'].append('Test error')
        
        report = self.service.get_analysis_report()
        
        self.assertEqual(report['folders_analyzed'], 10)
        self.assertEqual(report['processes_identified'], 8)
        self.assertIn('Test error', report['mapping_errors'])
        
        # Ensure it's a copy
        report['folders_analyzed'] = 20
        self.assertEqual(self.service.analysis_report['folders_analyzed'], 10)


class DocumentCategorizationServiceTest(TestCase):
    """Test cases for DocumentCategorizationService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = DocumentCategorizationService()
    
    def test_categorize_process_map_documents(self):
        """Test categorization of process map documents."""
        test_cases = [
            ('process_map.pdf', 'process_map'),
            ('workflow_diagram.docx', 'process_map'),
            ('finance_process_flow.pdf', 'process_map'),
            ('flow_chart.png', 'process_map'),
            ('process map - finance.pdf', 'process_map'),
        ]
        
        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                doc_type, confidence = self.service.categorize_document(filename)
                self.assertEqual(doc_type, expected_type)
                self.assertGreater(confidence, 0.3)
    
    def test_categorize_procedure_documents(self):
        """Test categorization of procedure documents."""
        test_cases = [
            ('procedure_manual.pdf', 'procedure'),
            ('user_guide.docx', 'procedure'),
            ('work_instruction.pdf', 'procedure'),
            ('sop_finance.pdf', 'procedure'),
            ('manual - hr processes.pdf', 'procedure'),
        ]
        
        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                doc_type, confidence = self.service.categorize_document(filename)
                self.assertEqual(doc_type, expected_type)
                self.assertGreater(confidence, 0.3)
    
    def test_categorize_risk_register_documents(self):
        """Test categorization of risk register documents."""
        test_cases = [
            ('risk_register.xlsx', 'risk_register'),
            ('risk_assessment.pdf', 'risk_register'),
            ('opportunity_register.xlsx', 'risk_register'),
            ('risk_and_opportunity_register.pdf', 'risk_register'),
            ('hazard_register.docx', 'risk_register'),
        ]
        
        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                doc_type, confidence = self.service.categorize_document(filename)
                self.assertEqual(doc_type, expected_type)
                self.assertGreater(confidence, 0.3)
    
    def test_categorize_uncategorized_documents(self):
        """Test categorization of documents that don't match patterns."""
        test_cases = [
            'random_document.pdf',
            'meeting_notes.docx',
            'budget_report.xlsx',
            'unknown_file.txt',
        ]
        
        for filename in test_cases:
            with self.subTest(filename=filename):
                doc_type, confidence = self.service.categorize_document(filename)
                self.assertIsNone(doc_type)
                self.assertLess(confidence, 0.3)
    
    def test_categorize_with_content_hint(self):
        """Test categorization using content hints."""
        # Document with ambiguous filename but clear content hint
        doc_type, confidence = self.service.categorize_document(
            'document.pdf',
            'This is a process map showing the workflow'
        )
        self.assertEqual(doc_type, 'process_map')
        self.assertGreater(confidence, 0.3)
        
        # Content hint should improve confidence
        doc_type1, conf1 = self.service.categorize_document('doc.pdf')
        doc_type2, conf2 = self.service.categorize_document('doc.pdf', 'procedure manual')
        
        self.assertIsNone(doc_type1)
        self.assertEqual(doc_type2, 'procedure')
        self.assertGreater(conf2, conf1)
    
    def test_categorize_documents_batch(self):
        """Test batch categorization of documents."""
        documents = [
            {'filename': 'process_map.pdf', 'content_hint': ''},
            {'filename': 'manual.docx', 'content_hint': 'user guide'},
            {'filename': 'risk.xlsx', 'content_hint': 'risk assessment'},
            {'filename': 'unknown.txt', 'content_hint': ''},
        ]
        
        result = self.service.categorize_documents_batch(documents)
        
        self.assertEqual(len(result), 4)
        
        # Check categorization results
        self.assertEqual(result[0]['document_type'], 'process_map')
        self.assertEqual(result[1]['document_type'], 'procedure')
        self.assertEqual(result[2]['document_type'], 'risk_register')
        self.assertIsNone(result[3]['document_type'])
        
        # Check that original data is preserved
        for i, doc in enumerate(result):
            self.assertEqual(doc['filename'], documents[i]['filename'])
            self.assertIn('confidence', doc)
    
    def test_calculate_pattern_score(self):
        """Test pattern score calculation."""
        patterns = [r'process[\s_-]*map', r'workflow', r'flow[\s_-]*chart']
        
        # Exact match
        score = self.service._calculate_pattern_score('process map document', patterns)
        self.assertGreater(score, 0.5)
        
        # Partial match
        score = self.service._calculate_pattern_score('workflow diagram', patterns)
        self.assertGreater(score, 0.5)
        
        # No match
        score = self.service._calculate_pattern_score('random document', patterns)
        self.assertEqual(score, 0.0)
        
        # Empty text
        score = self.service._calculate_pattern_score('', patterns)
        self.assertEqual(score, 0.0)
        
        # Empty patterns
        score = self.service._calculate_pattern_score('process map', [])
        self.assertEqual(score, 0.0)
    
    def test_categorization_report_tracking(self):
        """Test that categorization report is properly tracked."""
        # Process some documents
        self.service.categorize_document('process_map.pdf')
        self.service.categorize_document('manual.docx')
        self.service.categorize_document('unknown.txt')
        
        report = self.service.get_categorization_report()
        
        self.assertEqual(report['documents_processed'], 3)
        self.assertEqual(report['documents_categorized'], 2)
        self.assertEqual(report['type_distribution']['process_map'], 1)
        self.assertEqual(report['type_distribution']['procedure'], 1)
        self.assertEqual(report['type_distribution']['uncategorized'], 1)
        
        # Check uncategorized documents list
        self.assertEqual(len(report['uncategorized_documents']), 1)
        self.assertEqual(report['uncategorized_documents'][0]['filename'], 'unknown.txt')
    
    def test_get_categorization_report(self):
        """Test getting categorization report."""
        # Simulate some categorization
        self.service.categorization_report['documents_processed'] = 10
        self.service.categorization_report['documents_categorized'] = 8
        self.service.categorization_report['categorization_errors'].append({'filename': 'error.pdf', 'error': 'Test error'})
        
        report = self.service.get_categorization_report()
        
        self.assertEqual(report['documents_processed'], 10)
        self.assertEqual(report['documents_categorized'], 8)
        self.assertEqual(len(report['categorization_errors']), 1)
        
        # Ensure it's a copy
        report['documents_processed'] = 20
        self.assertEqual(self.service.categorization_report['documents_processed'], 10)
    
    def test_invalid_regex_handling(self):
        """Test handling of invalid regex patterns."""
        # Mock invalid regex pattern
        with patch.object(self.service, 'DOCUMENT_PATTERNS', {'test': ['[invalid']}):
            doc_type, confidence = self.service.categorize_document('test.pdf')
            # Should not crash and return None
            self.assertIsNone(doc_type)
            self.assertEqual(confidence, 0.0)


class MigrationServicesIntegrationTest(TestCase):
    """Integration tests for migration services."""
    
    def setUp(self):
        """Set up test data."""
        self.folder_service = FolderAnalysisService()
        self.doc_service = DocumentCategorizationService()
    
    def test_services_integration(self):
        """Test integration between folder analysis and document categorization."""
        # Create mock folder analysis result
        folder_result = {
            'files_found': [
                {'name': 'budget_process_map.pdf', 'path': 'finance/budget_process_map.pdf'},
                {'name': 'hr_manual.docx', 'path': 'hr/hr_manual.docx'},
                {'name': 'risk_register.xlsx', 'path': 'risk/risk_register.xlsx'},
            ]
        }
        
        # Categorize the documents
        documents = [{'filename': f['name'], 'content_hint': ''} for f in folder_result['files_found']]
        categorized = self.doc_service.categorize_documents_batch(documents)
        
        # Verify categorization
        self.assertEqual(categorized[0]['document_type'], 'process_map')
        self.assertEqual(categorized[1]['document_type'], 'procedure')
        self.assertEqual(categorized[2]['document_type'], 'risk_register')
        
        # Verify all documents have confidence scores
        for doc in categorized:
            self.assertIn('confidence', doc)
            if doc['document_type']:
                self.assertGreater(doc['confidence'], 0.3)