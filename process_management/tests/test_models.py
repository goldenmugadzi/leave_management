from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from process_management.models import ProcessDepartment, Process, ProcessDocument
from it.users.models import Regions, UserProfile


class ProcessDepartmentModelTest(TestCase):
    """Test cases for ProcessDepartment model"""

    def setUp(self):
        """Set up test data"""
        self.department_data = {
            'name': 'Test Department',
            'description': 'Test department description',
            'order': 1
        }

    def test_create_process_department(self):
        """Test creating a ProcessDepartment instance"""
        department = ProcessDepartment.objects.create(**self.department_data)
        
        self.assertEqual(department.name, 'Test Department')
        self.assertEqual(department.description, 'Test department description')
        self.assertEqual(department.order, 1)
        self.assertIsNotNone(department.created_at)
        self.assertIsNotNone(department.updated_at)

    def test_process_department_str_method(self):
        """Test the string representation of ProcessDepartment"""
        department = ProcessDepartment.objects.create(**self.department_data)
        self.assertEqual(str(department), 'Test Department')

    def test_process_department_unique_name(self):
        """Test that department names must be unique"""
        ProcessDepartment.objects.create(**self.department_data)
        
        # Try to create another department with the same name
        with self.assertRaises(IntegrityError):
            ProcessDepartment.objects.create(**self.department_data)

    def test_process_department_blank_description(self):
        """Test that description can be blank"""
        department_data = self.department_data.copy()
        department_data['description'] = ''
        
        department = ProcessDepartment.objects.create(**department_data)
        self.assertEqual(department.description, '')

    def test_process_department_default_order(self):
        """Test that order defaults to 0"""
        department_data = self.department_data.copy()
        del department_data['order']
        
        department = ProcessDepartment.objects.create(**department_data)
        self.assertEqual(department.order, 0)

    def test_process_department_ordering(self):
        """Test that departments are ordered by order field then name"""
        dept1 = ProcessDepartment.objects.create(name='B Department', order=2)
        dept2 = ProcessDepartment.objects.create(name='A Department', order=1)
        dept3 = ProcessDepartment.objects.create(name='C Department', order=1)
        
        departments = list(ProcessDepartment.objects.all())
        
        # Should be ordered by order field first, then by name
        self.assertEqual(departments[0], dept2)  # A Department (order=1)
        self.assertEqual(departments[1], dept3)  # C Department (order=1)
        self.assertEqual(departments[2], dept1)  # B Department (order=2)

    def test_process_department_clean_empty_name(self):
        """Test validation for empty name"""
        department = ProcessDepartment(name='   ', description='Test', order=1)
        
        with self.assertRaises(ValidationError) as context:
            department.clean()
        
        self.assertIn('name', context.exception.message_dict)
        self.assertEqual(context.exception.message_dict['name'], ['Department name cannot be empty'])

    def test_process_department_clean_negative_order(self):
        """Test validation for negative order"""
        department = ProcessDepartment(name='Test Dept', description='Test', order=-1)
        
        with self.assertRaises(ValidationError) as context:
            department.clean()
        
        self.assertIn('order', context.exception.message_dict)
        self.assertEqual(context.exception.message_dict['order'], ['Order must be a non-negative integer'])

    def test_process_department_clean_valid_data(self):
        """Test that clean passes with valid data"""
        department = ProcessDepartment(name='Valid Department', description='Test', order=1)
        
        # Should not raise any exception
        try:
            department.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError with valid data")

    def test_process_department_meta_options(self):
        """Test model meta options"""
        self.assertEqual(ProcessDepartment._meta.verbose_name, 'Process Department')
        self.assertEqual(ProcessDepartment._meta.verbose_name_plural, 'Process Departments')
        self.assertEqual(ProcessDepartment._meta.ordering, ['order', 'name'])


class ProcessModelTest(TestCase):
    """Test cases for Process model"""

    def setUp(self):
        """Set up test data"""
        self.department = ProcessDepartment.objects.create(
            name='Test Department',
            description='Test department description',
            order=1
        )
        
        # Create test region
        self.region = Regions.objects.create(region='Test Region', code='TR')
        
        # Create test user
        self.user = UserProfile.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.process_data = {
            'name': 'Test Process',
            'description': 'Test process description',
            'department': self.department,
            'region': self.region,
            'process_code': 'TP001',
            'created_by': self.user
        }

    def test_create_process(self):
        """Test creating a Process instance"""
        process = Process.objects.create(**self.process_data)
        
        self.assertEqual(process.name, 'Test Process')
        self.assertEqual(process.description, 'Test process description')
        self.assertEqual(process.department, self.department)
        self.assertEqual(process.region, self.region)

        self.assertEqual(process.process_code, 'TP001')
        self.assertEqual(process.created_by, self.user)
        self.assertTrue(process.is_active)
        self.assertIsNotNone(process.created_at)
        self.assertIsNotNone(process.updated_at)

    def test_process_str_method(self):
        """Test the string representation of Process"""
        process = Process.objects.create(**self.process_data)
        expected_str = f"Test Process (Test Department)"
        self.assertEqual(str(process), expected_str)

    def test_process_unique_process_code(self):
        """Test that process codes must be unique"""
        Process.objects.create(**self.process_data)
        
        # Try to create another process with the same process_code
        process_data_2 = self.process_data.copy()
        process_data_2['name'] = 'Another Process'
        
        with self.assertRaises(ValidationError):
            Process.objects.create(**process_data_2)

    def test_process_blank_process_code(self):
        """Test that process_code can be blank"""
        process_data = self.process_data.copy()
        process_data['process_code'] = ''
        
        process = Process.objects.create(**process_data)
        self.assertEqual(process.process_code, '')

    def test_process_default_is_active(self):
        """Test that is_active defaults to True"""
        process_data = self.process_data.copy()
        del process_data['process_code']  # Remove to avoid unique constraint
        
        process = Process.objects.create(**process_data)
        self.assertTrue(process.is_active)

    def test_process_ordering(self):
        """Test that processes are ordered by department order, department name, then process name"""
        dept1 = ProcessDepartment.objects.create(name='A Department', order=2)
        dept2 = ProcessDepartment.objects.create(name='B Department', order=1)
        
        process1 = Process.objects.create(
            name='Z Process',
            department=dept1,
            created_by=self.user
        )
        process2 = Process.objects.create(
            name='A Process',
            department=dept2,
            created_by=self.user
        )
        process3 = Process.objects.create(
            name='B Process',
            department=dept2,
            created_by=self.user
        )
        
        processes = list(Process.objects.all())
        
        # Should be ordered by department order first, then by process name within department
        self.assertEqual(processes[0], process2)  # A Process (B Department, order=1)
        self.assertEqual(processes[1], process3)  # B Process (B Department, order=1)
        self.assertEqual(processes[2], process1)  # Z Process (A Department, order=2)

    def test_process_clean_empty_name(self):
        """Test validation for empty name"""
        process = Process(
            name='   ',
            department=self.department,
            created_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            process.clean()
        
        self.assertIn('name', context.exception.message_dict)
        self.assertEqual(context.exception.message_dict['name'], ['Process name cannot be empty'])

    def test_process_clean_duplicate_process_code(self):
        """Test validation for duplicate process code"""
        # Create first process
        Process.objects.create(**self.process_data)
        
        # Try to create second process with same code
        process2 = Process(
            name='Another Process',
            department=self.department,
            process_code='TP001',
            created_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            process2.clean()
        
        self.assertIn('process_code', context.exception.message_dict)
        self.assertEqual(context.exception.message_dict['process_code'], ['Process code must be unique'])

    def test_process_clean_valid_data(self):
        """Test that clean passes with valid data"""
        process = Process(
            name='Valid Process',
            department=self.department,
            process_code='VP001',
            created_by=self.user
        )
        
        # Should not raise any exception
        try:
            process.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError with valid data")

    def test_process_optional_relationships(self):
        """Test that region and created_by are optional"""
        process_data = {
            'name': 'Minimal Process',
            'department': self.department
        }
        
        process = Process.objects.create(**process_data)
        self.assertIsNone(process.region)

        self.assertIsNone(process.created_by)

    def test_process_department_relationship(self):
        """Test the relationship with ProcessDepartment"""
        process = Process.objects.create(**self.process_data)
        
        # Test forward relationship
        self.assertEqual(process.department, self.department)
        
        # Test reverse relationship
        self.assertIn(process, self.department.processes.all())

    def test_get_documents_by_type(self):
        """Test get_documents_by_type method"""
        process = Process.objects.create(**self.process_data)
        
        # Initially should return empty dict
        documents = process.get_documents_by_type()
        self.assertEqual(documents, {})

    def test_has_document_methods(self):
        """Test has_process_map, has_procedure, has_risk_register methods"""
        process = Process.objects.create(**self.process_data)
        
        # Initially should all return False
        self.assertFalse(process.has_process_map())
        self.assertFalse(process.has_procedure())
        self.assertFalse(process.has_risk_register())

    def test_process_meta_options(self):
        """Test model meta options"""
        self.assertEqual(Process._meta.verbose_name, 'Process')
        self.assertEqual(Process._meta.verbose_name_plural, 'Processes')
        self.assertEqual(Process._meta.ordering, ['department__order', 'department__name', 'name'])


class ProcessDocumentModelTest(TestCase):
    """Test cases for ProcessDocument model"""

    def setUp(self):
        """Set up test data"""
        self.department = ProcessDepartment.objects.create(
            name='Test Department',
            description='Test department description',
            order=1
        )
        
        self.user = UserProfile.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.process = Process.objects.create(
            name='Test Process',
            description='Test process description',
            department=self.department,
            created_by=self.user
        )
        
        # Create a test file
        self.test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        self.document_data = {
            'process': self.process,
            'document_type': 'process_map',
            'file': self.test_file,
            'filename': 'test_document.pdf',
            'version': '1.0',
            'uploaded_by': self.user
        }

    def test_create_process_document(self):
        """Test creating a ProcessDocument instance"""
        document = ProcessDocument.objects.create(**self.document_data)
        
        self.assertEqual(document.process, self.process)
        self.assertEqual(document.document_type, 'process_map')
        self.assertEqual(document.filename, 'test_document.pdf')
        self.assertEqual(document.version, '1.0')
        self.assertEqual(document.uploaded_by, self.user)
        self.assertTrue(document.is_current)
        self.assertIsNotNone(document.uploaded_at)

    def test_process_document_str_method(self):
        """Test the string representation of ProcessDocument"""
        document = ProcessDocument.objects.create(**self.document_data)
        expected_str = f"Process Map - Test Process (v1.0)"
        self.assertEqual(str(document), expected_str)

    def test_process_document_choices(self):
        """Test document type choices"""
        expected_choices = [
            ('process_map', 'Process Map'),
            ('procedure', 'Procedure'),
            ('risk_register', 'Risk and Opportunity Register'),
        ]
        self.assertEqual(ProcessDocument.DOCUMENT_TYPES, expected_choices)

    def test_process_document_default_values(self):
        """Test default values"""
        document_data = self.document_data.copy()
        del document_data['version']  # Remove version to test default
        
        document = ProcessDocument.objects.create(**document_data)
        self.assertEqual(document.version, '1.0')
        self.assertTrue(document.is_current)

    def test_process_document_ordering(self):
        """Test that documents are ordered by uploaded_at descending"""
        doc1 = ProcessDocument.objects.create(**self.document_data)
        
        # Create second document with different file
        test_file2 = SimpleUploadedFile(
            "test_document2.pdf",
            b"file_content2",
            content_type="application/pdf"
        )
        document_data2 = self.document_data.copy()
        document_data2['file'] = test_file2
        document_data2['filename'] = 'test_document2.pdf'
        document_data2['document_type'] = 'procedure'
        doc2 = ProcessDocument.objects.create(**document_data2)
        
        documents = list(ProcessDocument.objects.all())
        
        # Should be ordered by uploaded_at descending (newest first)
        self.assertEqual(documents[0], doc2)
        self.assertEqual(documents[1], doc1)

    def test_process_document_clean_empty_filename(self):
        """Test validation for empty filename"""
        document = ProcessDocument(
            process=self.process,
            document_type='process_map',
            file=self.test_file,
            filename='   ',
            uploaded_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            document.clean()
        
        self.assertIn('filename', context.exception.message_dict)
        self.assertEqual(context.exception.message_dict['filename'], ['Filename cannot be empty'])

    def test_process_document_clean_empty_version(self):
        """Test validation for empty version"""
        document = ProcessDocument(
            process=self.process,
            document_type='process_map',
            file=self.test_file,
            filename='test.pdf',
            version='   ',
            uploaded_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            document.clean()
        
        self.assertIn('version', context.exception.message_dict)
        self.assertEqual(context.exception.message_dict['version'], ['Version cannot be empty'])

    def test_process_document_unique_current_per_type(self):
        """Test that only one current document can exist per type per process"""
        # Create first document
        ProcessDocument.objects.create(**self.document_data)
        
        # Try to create second current document of same type
        test_file2 = SimpleUploadedFile(
            "test_document2.pdf",
            b"file_content2",
            content_type="application/pdf"
        )
        document_data2 = self.document_data.copy()
        document_data2['file'] = test_file2
        document_data2['filename'] = 'test_document2.pdf'
        document_data2['is_current'] = True
        
        document2 = ProcessDocument(**document_data2)
        
        with self.assertRaises(ValidationError) as context:
            document2.clean()
        
        self.assertIn('is_current', context.exception.message_dict)

    def test_process_document_save_marks_others_not_current(self):
        """Test that saving a current document marks others as not current"""
        # Create first document
        doc1 = ProcessDocument.objects.create(**self.document_data)
        self.assertTrue(doc1.is_current)
        
        # Create second document of same type
        test_file2 = SimpleUploadedFile(
            "test_document2.pdf",
            b"file_content2",
            content_type="application/pdf"
        )
        document_data2 = self.document_data.copy()
        document_data2['file'] = test_file2
        document_data2['filename'] = 'test_document2.pdf'
        document_data2['version'] = '2.0'
        document_data2['is_current'] = True
        
        doc2 = ProcessDocument.objects.create(**document_data2)
        
        # Refresh first document from database
        doc1.refresh_from_db()
        
        # First document should no longer be current
        self.assertFalse(doc1.is_current)
        self.assertTrue(doc2.is_current)

    def test_process_document_different_types_can_be_current(self):
        """Test that different document types can both be current"""
        # Create process map
        doc1 = ProcessDocument.objects.create(**self.document_data)
        
        # Create procedure
        test_file2 = SimpleUploadedFile(
            "test_procedure.pdf",
            b"procedure_content",
            content_type="application/pdf"
        )
        document_data2 = self.document_data.copy()
        document_data2['file'] = test_file2
        document_data2['filename'] = 'test_procedure.pdf'
        document_data2['document_type'] = 'procedure'
        
        doc2 = ProcessDocument.objects.create(**document_data2)
        
        # Both should be current since they're different types
        self.assertTrue(doc1.is_current)
        self.assertTrue(doc2.is_current)

    def test_get_file_extension(self):
        """Test get_file_extension method"""
        document = ProcessDocument.objects.create(**self.document_data)
        self.assertEqual(document.get_file_extension(), 'pdf')
        
        # Test with no extension
        document.filename = 'test_file'
        self.assertEqual(document.get_file_extension(), '')

    def test_get_file_size_display(self):
        """Test get_file_size_display method"""
        document = ProcessDocument.objects.create(**self.document_data)
        size_display = document.get_file_size_display()
        
        # Should return a string with size and unit
        self.assertIsInstance(size_display, str)
        self.assertTrue(any(unit in size_display for unit in ['bytes', 'KB', 'MB', 'GB']))

    def test_process_relationship(self):
        """Test the relationship with Process"""
        document = ProcessDocument.objects.create(**self.document_data)
        
        # Test forward relationship
        self.assertEqual(document.process, self.process)
        
        # Test reverse relationship
        self.assertIn(document, self.process.documents.all())

    def test_process_document_meta_options(self):
        """Test model meta options"""
        self.assertEqual(ProcessDocument._meta.verbose_name, 'Process Document')
        self.assertEqual(ProcessDocument._meta.verbose_name_plural, 'Process Documents')
        self.assertEqual(ProcessDocument._meta.ordering, ['-uploaded_at'])

    def test_process_has_document_methods_with_documents(self):
        """Test Process model document check methods with actual documents"""
        # Initially no documents
        self.assertFalse(self.process.has_process_map())
        self.assertFalse(self.process.has_procedure())
        self.assertFalse(self.process.has_risk_register())
        
        # Add process map
        ProcessDocument.objects.create(**self.document_data)
        self.assertTrue(self.process.has_process_map())
        self.assertFalse(self.process.has_procedure())
        self.assertFalse(self.process.has_risk_register())
        
        # Add procedure
        test_file2 = SimpleUploadedFile(
            "test_procedure.pdf",
            b"procedure_content",
            content_type="application/pdf"
        )
        document_data2 = self.document_data.copy()
        document_data2['file'] = test_file2
        document_data2['filename'] = 'test_procedure.pdf'
        document_data2['document_type'] = 'procedure'
        
        ProcessDocument.objects.create(**document_data2)
        self.assertTrue(self.process.has_process_map())
        self.assertTrue(self.process.has_procedure())
        self.assertFalse(self.process.has_risk_register())

    def test_get_documents_by_type_with_documents(self):
        """Test get_documents_by_type method with actual documents"""
        # Add documents
        doc1 = ProcessDocument.objects.create(**self.document_data)
        
        test_file2 = SimpleUploadedFile(
            "test_procedure.pdf",
            b"procedure_content",
            content_type="application/pdf"
        )
        document_data2 = self.document_data.copy()
        document_data2['file'] = test_file2
        document_data2['filename'] = 'test_procedure.pdf'
        document_data2['document_type'] = 'procedure'
        
        doc2 = ProcessDocument.objects.create(**document_data2)
        
        documents = self.process.get_documents_by_type()
        
        self.assertEqual(documents['process_map'], doc1)
        self.assertEqual(documents['procedure'], doc2)
        self.assertNotIn('risk_register', documents)