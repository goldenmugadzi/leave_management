# Change Requests Testing Guide

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Writing Tests](#writing-tests)
6. [Test Data Management](#test-data-management)
7. [Continuous Integration](#continuous-integration)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [Troubleshooting](#troubleshooting)

## Overview

The Change Requests system includes a comprehensive test suite that covers all aspects of the application, from individual model methods to complete user workflows. This guide explains how to run, write, and maintain tests for the system.

## Test Structure

```
it/change_requests/tests/
├── __init__.py              # Test package initialization
├── test_models.py           # Model tests
├── test_views.py            # View and helper function tests
├── test_integration.py      # Integration and workflow tests
└── test_constants.py        # Constants and configuration tests
```

### Test File Organization

- **`test_models.py`**: Tests for all model classes, methods, and database operations
- **`test_views.py`**: Tests for view functions, helper functions, and business logic
- **`test_integration.py`**: Tests for complete user workflows and system integration
- **`test_constants.py`**: Tests for constants, configuration, and application settings

## Running Tests

### Prerequisites

Ensure you have the test environment set up:

```bash
# Activate virtual environment
source /var/www/env-beii/bin/activate

# Install test dependencies
pip install -r requirements.txt
```

### Running All Tests

```bash
# Run all change requests tests
python manage.py test it.change_requests.tests

# Run with verbose output
python manage.py test it.change_requests.tests -v 2

# Run with coverage report
coverage run --source='.' manage.py test it.change_requests.tests
coverage report
coverage html  # Generate HTML coverage report
```

### Running Specific Test Files

```bash
# Run model tests only
python manage.py test it.change_requests.tests.test_models

# Run view tests only
python manage.py test it.change_requests.tests.test_views

# Run integration tests only
python manage.py test it.change_requests.tests.test_integration

# Run constants tests only
python manage.py test it.change_requests.tests.test_constants
```

### Running Specific Test Classes

```bash
# Run specific test class
python manage.py test it.change_requests.tests.test_models.ChangeRequestModelTestCase

# Run specific test method
python manage.py test it.change_requests.tests.test_models.ChangeRequestModelTestCase.test_soft_delete_functionality
```

### Running Tests with Different Options

```bash
# Run tests in parallel (if supported)
python manage.py test it.change_requests.tests --parallel

# Run tests with specific database
python manage.py test it.change_requests.tests --settings=beii_v1.settings_test

# Run tests with keepdb (faster for development)
python manage.py test it.change_requests.tests --keepdb

# Run tests with debug mode
python manage.py test it.change_requests.tests --debug-mode
```

## Test Categories

### 1. Model Tests (`test_models.py`)

Tests for Django models and database operations:

#### ChangeRequestModelTestCase
- Model creation and field validation
- Soft delete functionality
- String representation
- Model ordering and relationships

#### NewProfileModelTestCase
- Profile creation and validation
- String representation
- Field constraints

#### CRApprovalModelTestCase
- Approval creation and tracking
- String representation
- Relationship validation

#### ProfileChangeModelTestCase
- Profile change creation
- Role assignments
- String representation

#### ProfileDeactivationModelTestCase
- Deactivation creation
- Audit trail
- String representation

### 2. View Tests (`test_views.py`)

Tests for view functions and helper methods:

#### ValidationFunctionsTestCase
- Input validation logic
- Error message generation
- Field length validation
- Required field checking

#### SanitizationFunctionsTestCase
- XSS prevention
- Input sanitization
- Whitespace handling
- Data type preservation

#### PermissionFunctionsTestCase
- Access control logic
- Permission checking
- Role-based permissions
- Creator permissions

#### HelperFunctionsTestCase
- Data preparation functions
- Approval status logic
- Query optimization
- Caching functionality

#### QueryOptimizationTestCase
- Database query optimization
- Filter application
- Performance improvements

#### CachingTestCase
- Cache hit/miss scenarios
- Cache invalidation
- Performance optimization

### 3. Integration Tests (`test_integration.py`)

Tests for complete user workflows:

#### ChangeRequestWorkflowTestCase
- Complete new profile workflow
- Approval workflow
- Soft delete and restore workflow
- Bulk operations workflow
- Permission workflow
- Validation workflow
- Approval status progression

#### SecurityIntegrationTestCase
- CSRF protection
- XSS prevention
- Authentication requirements
- Authorization checks

### 4. Constants Tests (`test_constants.py`)

Tests for application configuration:

#### ConstantsTestCase
- Change types validation
- Approval roles validation
- Field length limits
- Error and success messages
- Cache settings
- URL patterns
- Logging configuration

## Writing Tests

### Test Class Structure

```python
class TestCaseName(TestCase):
    """Test cases for specific functionality"""
    
    def setUp(self):
        """Set up test data before each test"""
        # Create test data
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_specific_functionality(self):
        """Test specific functionality with descriptive name"""
        # Arrange: Set up test data
        # Act: Perform the action being tested
        # Assert: Verify the expected outcome
        self.assertEqual(actual_result, expected_result)
    
    def tearDown(self):
        """Clean up after each test (if needed)"""
        # Clean up test data
        pass
```

### Test Method Naming

Use descriptive names that explain what is being tested:

```python
def test_soft_delete_marks_record_as_deleted(self):
    """Test that soft delete marks record as deleted"""

def test_validation_rejects_empty_required_fields(self):
    """Test that validation rejects empty required fields"""

def test_permission_check_allows_creator_access(self):
    """Test that permission check allows creator access"""
```

### Assertions

Use appropriate assertions for different scenarios:

```python
# Equality assertions
self.assertEqual(actual, expected)
self.assertNotEqual(actual, expected)

# Boolean assertions
self.assertTrue(condition)
self.assertFalse(condition)

# Membership assertions
self.assertIn(item, container)
self.assertNotIn(item, container)

# Exception assertions
self.assertRaises(Exception, function, args)

# Database assertions
self.assertEqual(Model.objects.count(), expected_count)
self.assertTrue(Model.objects.filter(field=value).exists())
```

### Mocking

Use mocking for external dependencies:

```python
from unittest.mock import patch, MagicMock

@patch('it.change_requests.views.cache')
def test_cached_user_data_cache_hit(self, mock_cache):
    """Test cached user data when cache hit"""
    # Mock cache hit
    mock_cache.get.return_value = {'data': 'cached'}
    
    result = get_cached_user_data('testuser')
    
    self.assertEqual(result, {'data': 'cached'})
    mock_cache.get.assert_called_once_with('user_data_testuser')
```

### Test Data Factories

Create reusable test data:

```python
def create_test_user(username='testuser'):
    """Create a test user with default values"""
    return User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='testpass123'
    )

def create_test_change_request(user, cr_id='CR001'):
    """Create a test change request"""
    return ChangeRequest.objects.create(
        cr_id=cr_id,
        change_type='NEW_PROFILE',
        change_reason='Test reason',
        change_description='Test description',
        created_by=user,
        # ... other required fields
    )
```

## Test Data Management

### Database Isolation

Each test runs in isolation with its own database transaction:

```python
class TestCase(TestCase):
    def setUp(self):
        """Each test gets fresh data"""
        self.user = create_test_user()
    
    def test_one(self):
        """This test won't affect test_two"""
        # Test implementation
    
    def test_two(self):
        """This test won't see changes from test_one"""
        # Test implementation
```

### Test Data Cleanup

Django automatically handles test data cleanup, but you can add custom cleanup:

```python
def tearDown(self):
    """Clean up any external resources"""
    # Clean up files, cache, etc.
    cache.clear()
```

### Test Database Configuration

Configure test database settings:

```python
# settings_test.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python manage.py test it.change_requests.tests
    
    - name: Run coverage
      run: |
        coverage run --source='.' manage.py test it.change_requests.tests
        coverage report
        coverage xml
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh 'python manage.py test it.change_requests.tests'
            }
        }
        
        stage('Coverage') {
            steps {
                sh 'coverage run --source="." manage.py test it.change_requests.tests'
                sh 'coverage report'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
            }
        }
    }
}
```

## Performance Testing

### Load Testing

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
import time

class PerformanceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_change_request_creation_performance(self):
        """Test that change request creation is fast enough"""
        start_time = time.time()
        
        response = self.client.post('/change_requests/create_new_profile', {
            'change_reason': 'Test reason',
            'change_description': 'Test description',
            # ... other fields
        })
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assert response is successful
        self.assertEqual(response.status_code, 302)
        
        # Assert performance is acceptable (less than 2 seconds)
        self.assertLess(duration, 2.0)
```

### Database Query Testing

```python
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.test.utils import CaptureQueries

class DatabasePerformanceTestCase(TestCase):
    def test_change_request_list_query_count(self):
        """Test that change request list doesn't use too many queries"""
        # Create test data
        for i in range(10):
            create_test_change_request(f'CR{i:03d}')
        
        with CaptureQueries(connection) as queries:
            # Perform the action
            change_requests = ChangeRequest.objects.all()
            list(change_requests)  # Force evaluation
        
        # Assert query count is reasonable (N+1 query problem prevention)
        self.assertLess(len(queries), 5)
```

## Security Testing

### CSRF Protection Testing

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User

class SecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_csrf_protection(self):
        """Test that CSRF protection is working"""
        response = self.client.post('/change_requests/create_new_profile', {
            'change_reason': 'Test reason',
            'change_description': 'Test description',
        })
        
        # Should be redirected or show CSRF error
        self.assertIn(response.status_code, [302, 403])
```

### XSS Prevention Testing

```python
def test_xss_prevention(self):
    """Test that XSS attacks are prevented"""
    malicious_input = '<script>alert("XSS")</script>'
    
    response = self.client.post('/change_requests/create_new_profile', {
        'change_reason': malicious_input,
        'change_description': 'Test description',
        # ... other fields
    })
    
    # Should not cause XSS
    self.assertIn(response.status_code, [200, 302])
    
    # If change request was created, verify input was sanitized
    change_request = ChangeRequest.objects.filter(
        change_reason__contains='<script>'
    ).first()
    self.assertIsNone(change_request)
```

### Permission Testing

```python
def test_unauthorized_access(self):
    """Test that unauthorized users cannot access protected endpoints"""
    # Don't login
    response = self.client.get('/change_requests/change_request_index')
    
    # Should redirect to login
    self.assertEqual(response.status_code, 302)
    self.assertIn('/login', response.url)
```

## Troubleshooting

### Common Test Issues

#### 1. Database Issues

**Problem**: Tests fail with database errors
**Solution**:
```bash
# Check database configuration
python manage.py check --database default

# Reset test database
python manage.py test --keepdb it.change_requests.tests
```

#### 2. Import Errors

**Problem**: Import errors in tests
**Solution**:
```python
# Use relative imports
from ..models import ChangeRequest
from ..views import validate_change_request_data
```

#### 3. Test Data Conflicts

**Problem**: Tests interfere with each other
**Solution**:
```python
def setUp(self):
    """Use unique data for each test"""
    self.user = User.objects.create_user(
        username=f'testuser_{self.id()}',
        email=f'test_{self.id()}@example.com',
        password='testpass123'
    )
```

#### 4. Mock Issues

**Problem**: Mocks not working as expected
**Solution**:
```python
# Use proper patch paths
@patch('it.change_requests.views.cache')  # Correct
# Not: @patch('cache')  # Incorrect
```

### Debugging Tests

#### Enable Debug Mode

```python
# In test method
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use Django's debug mode
from django.test import override_settings

@override_settings(DEBUG=True)
def test_with_debug(self):
    # Test implementation
```

#### Print Debug Information

```python
def test_debug_example(self):
    """Example of debugging test issues"""
    result = some_function()
    print(f"Debug: result = {result}")  # Will show in test output
    self.assertEqual(result, expected)
```

#### Use Django Debug Toolbar

```python
# In test settings
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

### Test Performance Issues

#### Slow Tests

**Problem**: Tests are running slowly
**Solutions**:
- Use `--keepdb` flag for faster database setup
- Use `@override_settings` to disable unnecessary features
- Use `setUpClass` for expensive setup operations
- Use mocking to avoid external dependencies

#### Memory Issues

**Problem**: Tests consume too much memory
**Solutions**:
- Use `tearDown` to clean up resources
- Use `setUpClass` and `tearDownClass` for class-level setup
- Avoid creating large amounts of test data
- Use database transactions for isolation

### Best Practices

1. **Keep Tests Fast**: Aim for tests that run in seconds, not minutes
2. **Make Tests Independent**: Each test should be able to run in isolation
3. **Use Descriptive Names**: Test names should clearly describe what is being tested
4. **Test Edge Cases**: Include tests for boundary conditions and error scenarios
5. **Mock External Dependencies**: Don't rely on external services in tests
6. **Maintain Test Coverage**: Aim for high test coverage but focus on quality
7. **Review Test Code**: Treat test code with the same care as production code
8. **Document Complex Tests**: Add comments for complex test logic

---

*This testing guide should be updated as the test suite evolves and new testing patterns are established.*
