"""
Unit tests for constants and configuration
"""
from django.test import TestCase
from it.change_requests import constants


class ConstantsTestCase(TestCase):
    """Test cases for constants module"""
    
    def test_change_types_defined(self):
        """Test that change types are properly defined"""
        self.assertIn('NEW_PROFILE', constants.CHANGE_TYPES)
        self.assertIn('PROFILE_MODIFICATION', constants.CHANGE_TYPES)
        self.assertIn('PROFILE_DEACTIVATION', constants.CHANGE_TYPES)
        
        self.assertEqual(constants.CHANGE_TYPES['NEW_PROFILE'], 'New Profile')
        self.assertEqual(constants.CHANGE_TYPES['PROFILE_MODIFICATION'], 'Profile Modification')
        self.assertEqual(constants.CHANGE_TYPES['PROFILE_DEACTIVATION'], 'Profile Deactivation')
    
    def test_approval_roles_defined(self):
        """Test that approval roles are properly defined"""
        self.assertIn('SECTION_HEAD', constants.APPROVAL_ROLES)
        self.assertIn('IT_SECTION_HEAD', constants.APPROVAL_ROLES)
        
        self.assertEqual(constants.APPROVAL_ROLES['SECTION_HEAD'], 'section_head')
        self.assertEqual(constants.APPROVAL_ROLES['IT_SECTION_HEAD'], 'it_section_head')
    
    def test_approval_status_defined(self):
        """Test that approval status values are properly defined"""
        self.assertIn('PENDING', constants.APPROVAL_STATUS)
        self.assertIn('APPROVED', constants.APPROVAL_STATUS)
        self.assertIn('REJECTED', constants.APPROVAL_STATUS)
        
        self.assertEqual(constants.APPROVAL_STATUS['PENDING'], 'Pending')
        self.assertEqual(constants.APPROVAL_STATUS['APPROVED'], 'Approved')
        self.assertEqual(constants.APPROVAL_STATUS['REJECTED'], 'Rejected')
    
    def test_field_length_limits(self):
        """Test that field length limits are properly defined"""
        self.assertIsInstance(constants.MAX_DESCRIPTION_LENGTH, int)
        self.assertIsInstance(constants.MAX_REASON_LENGTH, int)
        self.assertIsInstance(constants.MAX_USERNAME_LENGTH, int)
        self.assertIsInstance(constants.MAX_NAME_LENGTH, int)
        self.assertIsInstance(constants.MAX_EMAIL_LENGTH, int)
        
        self.assertGreater(constants.MAX_DESCRIPTION_LENGTH, 0)
        self.assertGreater(constants.MAX_REASON_LENGTH, 0)
        self.assertGreater(constants.MAX_USERNAME_LENGTH, 0)
        self.assertGreater(constants.MAX_NAME_LENGTH, 0)
        self.assertGreater(constants.MAX_EMAIL_LENGTH, 0)
    
    def test_cache_settings(self):
        """Test that cache settings are properly defined"""
        self.assertIsInstance(constants.CACHE_TIMEOUT, int)
        self.assertIsInstance(constants.USER_DATA_CACHE_KEY_PREFIX, str)
        
        self.assertGreater(constants.CACHE_TIMEOUT, 0)
        self.assertGreater(len(constants.USER_DATA_CACHE_KEY_PREFIX), 0)
    
    def test_pagination_settings(self):
        """Test that pagination settings are properly defined"""
        self.assertIsInstance(constants.DEFAULT_PAGE_SIZE, int)
        self.assertIsInstance(constants.MAX_PAGE_SIZE, int)
        
        self.assertGreater(constants.DEFAULT_PAGE_SIZE, 0)
        self.assertGreater(constants.MAX_PAGE_SIZE, constants.DEFAULT_PAGE_SIZE)
    
    def test_error_messages_defined(self):
        """Test that error messages are properly defined"""
        required_error_keys = [
            'CHANGE_REQUEST_NOT_FOUND',
            'INSUFFICIENT_PERMISSIONS',
            'CANNOT_DELETE_APPROVED',
            'CANNOT_RESTORE',
            'VALIDATION_ERROR',
            'DUPLICATE_USERNAME',
            'REQUIRED_FIELD_MISSING',
            'FIELD_TOO_LONG'
        ]
        
        for key in required_error_keys:
            self.assertIn(key, constants.ERROR_MESSAGES)
            self.assertIsInstance(constants.ERROR_MESSAGES[key], str)
            self.assertGreater(len(constants.ERROR_MESSAGES[key]), 0)
    
    def test_success_messages_defined(self):
        """Test that success messages are properly defined"""
        required_success_keys = [
            'CHANGE_REQUEST_CREATED',
            'CHANGE_REQUEST_UPDATED',
            'CHANGE_REQUEST_DELETED',
            'CHANGE_REQUEST_RESTORED',
            'BULK_DELETE_SUCCESS',
            'APPROVAL_SUCCESS',
            'REJECTION_SUCCESS'
        ]
        
        for key in required_success_keys:
            self.assertIn(key, constants.SUCCESS_MESSAGES)
            self.assertIsInstance(constants.SUCCESS_MESSAGES[key], str)
            self.assertGreater(len(constants.SUCCESS_MESSAGES[key]), 0)
    
    def test_warning_messages_defined(self):
        """Test that warning messages are properly defined"""
        required_warning_keys = [
            'ALREADY_APPROVED',
            'NO_CHANGES_MADE'
        ]
        
        for key in required_warning_keys:
            self.assertIn(key, constants.WARNING_MESSAGES)
            self.assertIsInstance(constants.WARNING_MESSAGES[key], str)
            self.assertGreater(len(constants.WARNING_MESSAGES[key]), 0)
    
    def test_application_names_defined(self):
        """Test that application names are properly defined"""
        self.assertIn('CHANGE_REQUESTS', constants.APPLICATION_NAMES)
        self.assertIn('BUSINESS_EXCELLENCE', constants.APPLICATION_NAMES)
        
        self.assertEqual(constants.APPLICATION_NAMES['CHANGE_REQUESTS'], 'change_requests')
        self.assertEqual(constants.APPLICATION_NAMES['BUSINESS_EXCELLENCE'], 'BUSINESS EXCELLENCE')
    
    def test_database_query_settings(self):
        """Test that database query settings are properly defined"""
        self.assertIsInstance(constants.SELECT_RELATED_FIELDS, list)
        self.assertIsInstance(constants.PREFETCH_RELATED_FIELDS, list)
        
        self.assertGreater(len(constants.SELECT_RELATED_FIELDS), 0)
        self.assertGreater(len(constants.PREFETCH_RELATED_FIELDS), 0)
        
        # Check that all fields are strings
        for field in constants.SELECT_RELATED_FIELDS:
            self.assertIsInstance(field, str)
        
        for field in constants.PREFETCH_RELATED_FIELDS:
            self.assertIsInstance(field, str)
    
    def test_required_fields_defined(self):
        """Test that required fields are properly defined"""
        self.assertIsInstance(constants.REQUIRED_CHANGE_REQUEST_FIELDS, list)
        self.assertIsInstance(constants.REQUIRED_NEW_PROFILE_FIELDS, list)
        
        self.assertGreater(len(constants.REQUIRED_CHANGE_REQUEST_FIELDS), 0)
        self.assertGreater(len(constants.REQUIRED_NEW_PROFILE_FIELDS), 0)
        
        # Check that all fields are strings
        for field in constants.REQUIRED_CHANGE_REQUEST_FIELDS:
            self.assertIsInstance(field, str)
        
        for field in constants.REQUIRED_NEW_PROFILE_FIELDS:
            self.assertIsInstance(field, str)
    
    def test_url_patterns_defined(self):
        """Test that URL patterns are properly defined"""
        required_url_keys = [
            'CHANGE_REQUEST_INDEX',
            'CREATE_CHANGE_REQUEST',
            'UPDATE_CHANGE_REQUEST',
            'DELETE_CHANGE_REQUEST',
            'RESTORE_CHANGE_REQUEST',
            'BULK_DELETE_CHANGE_REQUESTS'
        ]
        
        for key in required_url_keys:
            self.assertIn(key, constants.URL_PATTERNS)
            self.assertIsInstance(constants.URL_PATTERNS[key], str)
            self.assertTrue(constants.URL_PATTERNS[key].startswith('/'))
    
    def test_log_levels_defined(self):
        """Test that log levels are properly defined"""
        required_log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        
        for level in required_log_levels:
            self.assertIn(level, constants.LOG_LEVELS)
            self.assertEqual(constants.LOG_LEVELS[level], level)
    
    def test_log_messages_defined(self):
        """Test that log messages are properly defined"""
        required_log_keys = [
            'CHANGE_REQUEST_CREATED',
            'CHANGE_REQUEST_UPDATED',
            'CHANGE_REQUEST_DELETED',
            'CHANGE_REQUEST_RESTORED',
            'BULK_DELETE',
            'PERMISSION_DENIED',
            'VALIDATION_ERROR',
            'APPROVAL_ACTION'
        ]
        
        for key in required_log_keys:
            self.assertIn(key, constants.LOG_MESSAGES)
            self.assertIsInstance(constants.LOG_MESSAGES[key], str)
            self.assertGreater(len(constants.LOG_MESSAGES[key]), 0)
    
    def test_constants_consistency(self):
        """Test that constants are consistent with each other"""
        # Test that required fields match expected field names
        expected_change_request_fields = ['change_reason', 'change_description']
        expected_new_profile_fields = ['username', 'first_name', 'last_name', 'email']
        
        self.assertEqual(set(constants.REQUIRED_CHANGE_REQUEST_FIELDS), set(expected_change_request_fields))
        self.assertEqual(set(constants.REQUIRED_NEW_PROFILE_FIELDS), set(expected_new_profile_fields))
        
        # Test that cache timeout is reasonable
        self.assertGreaterEqual(constants.CACHE_TIMEOUT, 60)  # At least 1 minute
        self.assertLessEqual(constants.CACHE_TIMEOUT, 3600)  # At most 1 hour
        
        # Test that field lengths are reasonable
        self.assertGreaterEqual(constants.MAX_REASON_LENGTH, 100)
        self.assertGreaterEqual(constants.MAX_DESCRIPTION_LENGTH, 500)
        self.assertGreaterEqual(constants.MAX_USERNAME_LENGTH, 5)
        self.assertGreaterEqual(constants.MAX_NAME_LENGTH, 10)
        self.assertGreaterEqual(constants.MAX_EMAIL_LENGTH, 10)
    
    def test_constants_importability(self):
        """Test that all constants can be imported without errors"""
        try:
            from it.change_requests.constants import (
                CHANGE_TYPES, APPROVAL_ROLES, APPROVAL_STATUS,
                MAX_DESCRIPTION_LENGTH, MAX_REASON_LENGTH,
                ERROR_MESSAGES, SUCCESS_MESSAGES, WARNING_MESSAGES,
                REQUIRED_CHANGE_REQUEST_FIELDS, REQUIRED_NEW_PROFILE_FIELDS,
                URL_PATTERNS, CACHE_TIMEOUT, USER_DATA_CACHE_KEY_PREFIX
            )
            self.assertTrue(True)  # If we get here, import was successful
        except ImportError as e:
            self.fail(f"Failed to import constants: {e}")
