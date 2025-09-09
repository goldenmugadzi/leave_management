"""
Tests for ProcessCreationStrategy class.
"""
from django.test import TestCase
from django.db import transaction
from unittest.mock import Mock, patch

from process_management.process_creation_strategy import (
    ProcessCreationStrategy, BusinessFunction, ProcessCandidate
)
from process_management.models import ProcessDepartment, Process


class TestProcessCreationStrategy(TestCase):
    """Test cases for ProcessCreationStrategy class."""
    
    def setUp(self):
        """Set up test data."""
        self.strategy = ProcessCreationStrategy()
        
        # Create test departments
        self.finance_dept = ProcessDepartment.objects.create(
            name='FINANCE',
            description='Finance Department',
            order=1
        )
        self.hr_dept = ProcessDepartment.objects.create(
            name='HUMAN RESOURCES AND ADMINISTRATION',
            description='HR Department',
            order=2
        )
        
        # Sample documents for testing
        self.sample_documents = [
            {
                'filename': 'procurement_procedure.pdf',
                'folder_path': 'finance/procurement',
                'content_hint': 'purchasing guidelines',
                'department': 'FINANCE'
            },
            {
                'filename': 'vendor_management_manual.docx',
                'folder_path': 'finance/procurement',
                'content_hint': 'supplier management',
                'department': 'FINANCE'
            },
            {
                'filename': 'safety_procedure.pdf',
                'folder_path': 'safety/procedures',
                'content_hint': 'health and safety guidelines',
                'department': 'SAFETY'
            },
            {
                'filename': 'employee_handbook.pdf',
                'folder_path': 'hr/policies',
                'content_hint': 'human resources policies',
                'department': 'HUMAN RESOURCES AND ADMINISTRATION'
            },
            {
                'filename': 'training_manual.docx',
                'folder_path': 'hr/training',
                'content_hint': 'staff development',
                'department': 'HUMAN RESOURCES AND ADMINISTRATION'
            }
        ]
    
    def test_analyze_business_functions(self):
        """Test business function analysis from documents."""
        functions = self.strategy.analyze_business_functions(self.sample_documents)
        
        # Should identify multiple business functions
        self.assertGreater(len(functions), 0)
        
        # Check that functions have required attributes
        for function in functions:
            self.assertIsInstance(function, BusinessFunction)
            self.assertIsInstance(function.name, str)
            self.assertIsInstance(function.documents, list)
            self.assertIsInstance(function.confidence, float)
            self.assertGreaterEqual(function.confidence, 0.0)
            self.assertLessEqual(function.confidence, 1.0)
        
        # Should group procurement documents together
        procurement_functions = [f for f in functions if 'procurement' in f.name]
        if procurement_functions:
            procurement_function = procurement_functions[0]
            self.assertGreaterEqual(len(procurement_function.documents), 2)
    
    def test_identify_document_functions(self):
        """Test document function identification."""
        doc = {
            'filename': 'procurement_procedure.pdf',
            'folder_path': 'finance/procurement',
            'content_hint': 'purchasing guidelines'
        }
        
        functions = self.strategy._identify_document_functions(doc)
        
        # Should identify procurement as a function
        self.assertIn('procurement', functions)
        self.assertGreater(functions['procurement'], 0.0)
    
    def test_infer_department_from_documents(self):
        """Test department inference from documents."""
        finance_docs = [doc for doc in self.sample_documents if doc.get('department') == 'FINANCE']
        
        department = self.strategy._infer_department_from_documents(finance_docs)
        
        self.assertEqual(department, 'FINANCE')
    
    def test_generate_process_name(self):
        """Test process name generation."""
        business_function = BusinessFunction(
            name='procurement',
            keywords=['procurement', 'purchase'],
            documents=[],
            department='FINANCE',
            confidence=0.8
        )
        
        name = self.strategy._generate_process_name(business_function)
        
        # Should include department code and function name
        self.assertIn('FIN', name)
        self.assertIn('Procurement', name)
    
    def test_generate_process_code(self):
        """Test process code generation."""
        business_function = BusinessFunction(
            name='procurement',
            keywords=['procurement', 'purchase'],
            documents=[],
            department='FINANCE',
            confidence=0.8
        )
        
        code = self.strategy._generate_process_code(business_function)
        
        # Should follow department-function-number format
        self.assertTrue(code.startswith('FIN-'))
        self.assertTrue(code.endswith('-001'))  # First process of this type
    
    def test_handle_duplicates(self):
        """Test duplicate handling for names and codes."""
        # Add existing process to trigger duplicate handling
        existing_process = Process.objects.create(
            name='FIN Procurement',
            process_code='FIN-PROC-001',
            department=self.finance_dept
        )
        
        # Reload existing processes
        self.strategy._load_existing_processes()
        
        # Try to create duplicate
        final_name, final_code = self.strategy._handle_duplicates(
            'FIN Procurement', 'FIN-PROC-001', 'FINANCE'
        )
        
        # Should have different name and code
        self.assertNotEqual(final_name, 'FIN Procurement')
        self.assertNotEqual(final_code, 'FIN-PROC-001')
        self.assertTrue(final_name.startswith('FIN Procurement'))
        self.assertTrue(final_code.startswith('FIN-PROC-'))
    
    def test_create_process_candidates(self):
        """Test process candidate creation."""
        # Create business functions
        functions = self.strategy.analyze_business_functions(self.sample_documents)
        
        # Create candidates
        candidates = self.strategy.create_process_candidates(functions)
        
        # Should create candidates for each function
        self.assertEqual(len(candidates), len(functions))
        
        # Check candidate attributes
        for candidate in candidates:
            self.assertIsInstance(candidate, ProcessCandidate)
            self.assertIsInstance(candidate.name, str)
            self.assertIsInstance(candidate.process_code, str)
            self.assertIsInstance(candidate.department, str)
            self.assertIsInstance(candidate.confidence, float)
    
    def test_create_processes_from_candidates(self):
        """Test actual process creation from candidates."""
        # Create business functions and candidates
        functions = self.strategy.analyze_business_functions(self.sample_documents)
        candidates = self.strategy.create_process_candidates(functions)
        
        # Create processes
        processes = self.strategy.create_processes_from_candidates(candidates)
        
        # Should create processes
        self.assertGreater(len(processes), 0)
        
        # Check that processes were saved to database
        for process in processes:
            self.assertIsNotNone(process.id)
            self.assertIsInstance(process.department, ProcessDepartment)
            
            # Verify process can be retrieved from database
            db_process = Process.objects.get(id=process.id)
            self.assertEqual(db_process.name, process.name)
            self.assertEqual(db_process.process_code, process.process_code)
    
    def test_get_or_create_department(self):
        """Test department creation and retrieval."""
        # Test existing department
        existing_dept = self.strategy._get_or_create_department('FINANCE')
        self.assertEqual(existing_dept, self.finance_dept)
        
        # Test new department creation
        new_dept = self.strategy._get_or_create_department('NEW DEPARTMENT')
        self.assertIsNotNone(new_dept.id)
        self.assertEqual(new_dept.name, 'NEW DEPARTMENT')
    
    def test_calculate_function_confidence(self):
        """Test function confidence calculation."""
        # High confidence case - many documents, specific function
        high_conf = self.strategy._calculate_function_confidence('procurement', self.sample_documents)
        
        # Low confidence case - few documents, generic function
        low_conf = self.strategy._calculate_function_confidence('operations', [self.sample_documents[0]])
        
        self.assertGreater(high_conf, low_conf)
        self.assertGreaterEqual(high_conf, 0.0)
        self.assertLessEqual(high_conf, 1.0)
    
    def test_analyze_document_types(self):
        """Test document type analysis."""
        with patch.object(self.strategy.document_categorization_service, 'categorize_document') as mock_categorize:
            # Mock categorization results
            mock_categorize.side_effect = [
                ('procedure', 0.8),
                ('procedure', 0.7),
                ('risk_register', 0.9)
            ]
            
            doc_types = self.strategy._analyze_document_types(self.sample_documents[:3])
            
            # Should count document types
            self.assertIn('procedure', doc_types)
            self.assertIn('risk_register', doc_types)
            self.assertEqual(doc_types['procedure'], 2)
            self.assertEqual(doc_types['risk_register'], 1)
    
    def test_generate_process_description(self):
        """Test process description generation."""
        business_function = BusinessFunction(
            name='procurement',
            keywords=['procurement', 'purchase'],
            documents=self.sample_documents[:2],
            department='FINANCE',
            confidence=0.8,
            document_types={'procedure': 2}
        )
        
        candidate = ProcessCandidate(
            name='FIN Procurement',
            process_code='FIN-PROC-001',
            department='FINANCE',
            business_function=business_function,
            documents=business_function.documents,
            confidence=0.8
        )
        
        description = self.strategy._generate_process_description(candidate)
        
        # Should include key information
        self.assertIn('procurement', description)
        self.assertIn('FINANCE', description)
        self.assertIn('2 documents', description)
    
    def test_load_existing_processes(self):
        """Test loading existing processes to avoid duplicates."""
        # Create existing process
        existing_process = Process.objects.create(
            name='Test Process',
            process_code='TEST-001',
            department=self.finance_dept
        )
        
        # Create new strategy instance to test loading
        new_strategy = ProcessCreationStrategy()
        
        # Should have loaded existing codes and names
        self.assertIn('Test Process', new_strategy._existing_names)
        self.assertIn('TEST-001', new_strategy._existing_codes)
    
    def test_get_creation_report(self):
        """Test creation report generation."""
        # Analyze some documents to populate report
        self.strategy.analyze_business_functions(self.sample_documents)
        
        report = self.strategy.get_creation_report()
        
        # Should contain expected fields
        self.assertIn('documents_analyzed', report)
        self.assertIn('business_functions_identified', report)
        self.assertIn('processes_created', report)
        self.assertIn('function_distribution', report)
        
        # Should have analyzed documents
        self.assertEqual(report['documents_analyzed'], len(self.sample_documents))
    
    def test_business_function_keywords_coverage(self):
        """Test that business function keywords cover common business areas."""
        keywords = self.strategy.BUSINESS_FUNCTION_KEYWORDS
        
        # Should have key business functions
        expected_functions = [
            'procurement', 'safety_management', 'financial_management',
            'human_resources', 'operations', 'risk_management'
        ]
        
        for function in expected_functions:
            self.assertIn(function, keywords)
            self.assertIn('keywords', keywords[function])
            self.assertIn('weight', keywords[function])
    
    def test_department_codes_mapping(self):
        """Test department code mapping completeness."""
        codes = self.strategy.DEPARTMENT_CODES
        
        # Should have codes for common departments
        expected_departments = [
            'FINANCE', 'HUMAN RESOURCES AND ADMINISTRATION',
            'OPERATIONS AND MAINTENANCE', 'SAFETY'
        ]
        
        for dept in expected_departments:
            self.assertIn(dept, codes)
            self.assertIsInstance(codes[dept], str)
            self.assertGreater(len(codes[dept]), 0)
    
    def test_integration_full_workflow(self):
        """Test complete workflow from documents to processes."""
        # Run complete workflow
        functions = self.strategy.analyze_business_functions(self.sample_documents)
        candidates = self.strategy.create_process_candidates(functions)
        processes = self.strategy.create_processes_from_candidates(candidates)
        
        # Should have created processes
        self.assertGreater(len(processes), 0)
        
        # All processes should be valid
        for process in processes:
            self.assertIsNotNone(process.id)
            self.assertIsNotNone(process.name)
            self.assertIsNotNone(process.process_code)
            self.assertIsInstance(process.department, ProcessDepartment)
        
        # Get final report
        report = self.strategy.get_creation_report()
        self.assertEqual(report['processes_created'], len(processes))
        self.assertGreaterEqual(report['business_functions_identified'], 1)


class TestBusinessFunction(TestCase):
    """Test cases for BusinessFunction dataclass."""
    
    def test_business_function_creation(self):
        """Test BusinessFunction creation and attributes."""
        documents = [{'filename': 'test.pdf'}]
        
        function = BusinessFunction(
            name='test_function',
            keywords=['test', 'function'],
            documents=documents,
            department='TEST DEPT',
            confidence=0.8
        )
        
        self.assertEqual(function.name, 'test_function')
        self.assertEqual(function.keywords, ['test', 'function'])
        self.assertEqual(function.documents, documents)
        self.assertEqual(function.department, 'TEST DEPT')
        self.assertEqual(function.confidence, 0.8)
        self.assertEqual(function.document_types, {})  # Should initialize empty
    
    def test_business_function_post_init(self):
        """Test BusinessFunction post-initialization."""
        function = BusinessFunction(
            name='test',
            keywords=[],
            documents=[]
        )
        
        # document_types should be initialized as empty dict
        self.assertIsInstance(function.document_types, dict)
        self.assertEqual(len(function.document_types), 0)


class TestProcessCandidate(TestCase):
    """Test cases for ProcessCandidate dataclass."""
    
    def test_process_candidate_creation(self):
        """Test ProcessCandidate creation and attributes."""
        business_function = BusinessFunction(
            name='test_function',
            keywords=[],
            documents=[]
        )
        
        candidate = ProcessCandidate(
            name='Test Process',
            process_code='TEST-001',
            department='TEST DEPT',
            business_function=business_function,
            documents=[],
            confidence=0.8
        )
        
        self.assertEqual(candidate.name, 'Test Process')
        self.assertEqual(candidate.process_code, 'TEST-001')
        self.assertEqual(candidate.department, 'TEST DEPT')
        self.assertEqual(candidate.business_function, business_function)
        self.assertEqual(candidate.confidence, 0.8)
        self.assertFalse(candidate.duplicate_handling_applied)
        self.assertIsNone(candidate.original_name)
        self.assertIsNone(candidate.original_code)