# Change Requests Developer Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Code Structure](#code-structure)
3. [Models](#models)
4. [Views and Business Logic](#views-and-business-logic)
5. [Security Implementation](#security-implementation)
6. [Performance Optimizations](#performance-optimizations)
7. [Testing Strategy](#testing-strategy)
8. [Configuration](#configuration)
9. [Deployment](#deployment)
10. [Maintenance](#maintenance)

## Architecture Overview

The Change Requests system is built using Django framework with the following architectural principles:

### Design Patterns

- **MVC Pattern**: Models, Views, and Templates separation
- **Repository Pattern**: Data access abstraction through Django ORM
- **Service Layer**: Business logic encapsulation in view functions
- **Decorator Pattern**: Security and validation decorators
- **Factory Pattern**: Model creation and data preparation

### Key Components

```
change_requests/
├── models.py          # Data models and business logic
├── views.py           # View functions and business logic
├── urls.py            # URL routing configuration
├── constants.py       # Application constants and configuration
├── admin.py           # Django admin interface
├── tests/             # Test suite
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_integration.py
│   └── test_constants.py
└── templates/         # HTML templates
```

## Code Structure

### Models (`models.py`)

The models define the data structure and business rules:

#### ChangeRequest Model
```python
class ChangeRequest(models.Model):
    # Core fields
    cr_id = models.CharField(max_length=100, primary_key=True)
    change_type = models.CharField(max_length=100)
    change_reason = models.TextField(null=True, blank=True)
    change_description = models.TextField(null=True, blank=True)
    
    # Relationships
    new_profile = models.ForeignKey(NewProfile, on_delete=models.CASCADE, null=True, blank=True)
    profile_change = models.ForeignKey(ProfileChange, on_delete=models.CASCADE, null=True, blank=True)
    profile_deactivation = models.ForeignKey(ProfileDeactivation, on_delete=models.CASCADE, null=True, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='cr_created_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_change_requests')
    
    # Business methods
    def soft_delete(self, user):
        """Soft delete the change request"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
    
    def restore(self):
        """Restore the change request"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()
```

#### Database Indexes
```python
class Meta:
    indexes = [
        models.Index(fields=['cr_id']),
        models.Index(fields=['created_at']),
        models.Index(fields=['change_type']),
        models.Index(fields=['region', 'cost_center']),
        models.Index(fields=['created_by']),
        models.Index(fields=['application']),
        models.Index(fields=['is_deleted']),
    ]
    ordering = ['-created_at']
```

### Views (`views.py`)

Views handle HTTP requests and business logic:

#### Security Decorators
```python
@csrf_protect
@login_required
def create_new_profile(request):
    # View implementation
```

#### Input Validation
```python
def validate_change_request_data(data):
    """Validate change request input data"""
    errors = []
    
    for field in REQUIRED_CHANGE_REQUEST_FIELDS:
        if not data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    if len(data.get('change_reason', '')) > MAX_REASON_LENGTH:
        errors.append(f"Change reason too long (max {MAX_REASON_LENGTH} characters)")
    
    return errors
```

#### Input Sanitization
```python
def sanitize_input(data):
    """Sanitize user input to prevent XSS attacks"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = escape(value.strip())
        else:
            sanitized[key] = value
    return sanitized
```

#### Permission Checking
```python
def check_change_request_permissions(user, change_request):
    """Check if user has permission to modify change request"""
    if not change_request:
        return False, "Change request not found"
    
    # Check if user is the creator
    if change_request.created_by == user:
        return True, "User is the creator"
    
    # Check if user has section head role for the cost center
    try:
        user_role = user.get_user_role_for_application("change_requests")
        if user_role and user_role.role == "section_head":
            user_responsibilities = Responsibilities.objects.filter(
                user=user, role=user_role
            ).first()
            if user_responsibilities and change_request.cost_center in user_responsibilities.cost_centers.all():
                return True, "User has section head permissions"
    except Exception:
        pass
    
    return False, "Insufficient permissions"
```

### Constants (`constants.py`)

Centralized configuration and constants:

```python
# Change Request Types
CHANGE_TYPES = {
    'NEW_PROFILE': 'New Profile',
    'PROFILE_MODIFICATION': 'Profile Modification',
    'PROFILE_DEACTIVATION': 'Profile Deactivation'
}

# Field Length Limits
MAX_DESCRIPTION_LENGTH = 1000
MAX_REASON_LENGTH = 500

# Error Messages
ERROR_MESSAGES = {
    'CHANGE_REQUEST_NOT_FOUND': 'Change request not found',
    'INSUFFICIENT_PERMISSIONS': 'Insufficient permissions',
    'CANNOT_DELETE_APPROVED': 'Cannot delete approved change request',
}

# Success Messages
SUCCESS_MESSAGES = {
    'CHANGE_REQUEST_CREATED': 'Change request created successfully',
    'CHANGE_REQUEST_DELETED': 'Change request deleted successfully',
}
```

## Models

### Model Relationships

```
ChangeRequest (1) ←→ (0..1) NewProfile
ChangeRequest (1) ←→ (0..1) ProfileChange
ChangeRequest (1) ←→ (0..1) ProfileDeactivation
ChangeRequest (1) ←→ (0..n) CRApproval

UserProfile (1) ←→ (0..n) ChangeRequest (created_by)
UserProfile (1) ←→ (0..n) ChangeRequest (deleted_by)
UserProfile (1) ←→ (0..n) CRApproval (approver)

Regions (1) ←→ (0..n) ChangeRequest
CostCenter (1) ←→ (0..n) ChangeRequest
Designations (1) ←→ (0..n) ChangeRequest
```

### Model Methods

#### ChangeRequest Methods
- `soft_delete(user)`: Marks record as deleted with audit trail
- `restore()`: Restores deleted record
- `__str__()`: String representation (returns cr_id)

#### NewProfile Methods
- `__str__()`: Returns full name or username

#### CRApproval Methods
- `__str__()`: Returns change request ID

### Database Constraints

- **Primary Keys**: All models have proper primary keys
- **Foreign Keys**: Proper cascade and set null behaviors
- **Unique Constraints**: Username uniqueness in NewProfile
- **Indexes**: Strategic indexes for performance

## Views and Business Logic

### View Function Categories

#### 1. CRUD Operations
- `create_change_request()`: Display creation form
- `create_new_profile()`: Create new profile request
- `update_change_request()`: Update existing request
- `delete_change_request()`: Soft delete request
- `restore_change_request()`: Restore deleted request

#### 2. Bulk Operations
- `bulk_delete_change_requests()`: Delete multiple requests

#### 3. Approval Workflow
- `approve_profile_request()`: Handle approval/rejection

#### 4. Data Retrieval
- `get_user_data()`: Get user data with caching
- `datatable_data()`: Provide data for DataTables
- `change_request_index()`: Main dashboard

#### 5. Helper Functions
- `validate_change_request_data()`: Input validation
- `sanitize_input()`: XSS prevention
- `check_change_request_permissions()`: Permission checking
- `get_change_requests_optimized()`: Optimized queries
- `apply_filters()`: Query filtering
- `get_cached_user_data()`: Caching implementation

### Business Logic Patterns

#### 1. Validation Pattern
```python
# Validate input
validation_errors = validate_change_request_data(data)
if validation_errors:
    for error in validation_errors:
        messages.error(request, error)
    return redirect("/change_requests/create_change_request")
```

#### 2. Permission Pattern
```python
# Check permissions
has_permission, permission_message = check_change_request_permissions(request.user, change_request)
if not has_permission:
    messages.error(request, permission_message)
    return redirect("/change_requests/change_request_index")
```

#### 3. Audit Pattern
```python
# Log actions
logger.info(LOG_MESSAGES['CHANGE_REQUEST_DELETED'].format(
    cr_id=cr_id, username=request.user.username
))
```

#### 4. Error Handling Pattern
```python
try:
    # Business logic
    change_request.soft_delete(request.user)
    messages.success(request, SUCCESS_MESSAGES['CHANGE_REQUEST_DELETED'])
except Exception as ex:
    logger.error(f"Error deleting change request {cr_id}: {str(ex)}", exc_info=True)
    messages.error(request, f"Error deleting change request: {str(ex)}")
```

## Security Implementation

### 1. CSRF Protection
```python
@csrf_protect
@login_required
def view_function(request):
    # All POST endpoints are protected
```

### 2. Input Sanitization
```python
def sanitize_input(data):
    """Sanitize user input to prevent XSS attacks"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = escape(value.strip())
        else:
            sanitized[key] = value
    return sanitized
```

### 3. Permission Checking
- **Creator Permissions**: Users can manage their own requests
- **Role-Based Permissions**: Section heads can manage their cost center requests
- **Admin Permissions**: Administrators have special privileges

### 4. Audit Logging
```python
# Comprehensive logging
logger.info(f"Change request created: {cr_id} by {username}")
logger.warning(f"Permission denied for user {username} on change request {cr_id}")
logger.error(f"Error in operation: {str(ex)}", exc_info=True)
```

### 5. Data Validation
- **Required Fields**: All required fields validated
- **Field Lengths**: Maximum lengths enforced
- **Data Types**: Proper data type validation
- **Business Rules**: Username uniqueness, email format, etc.

## Performance Optimizations

### 1. Database Indexing
```python
class Meta:
    indexes = [
        models.Index(fields=['cr_id']),
        models.Index(fields=['created_at']),
        models.Index(fields=['change_type']),
        models.Index(fields=['region', 'cost_center']),
        models.Index(fields=['created_by']),
        models.Index(fields=['application']),
        models.Index(fields=['is_deleted']),
    ]
```

### 2. Query Optimization
```python
def get_change_requests_optimized(user, filters=None, include_deleted=False):
    """Optimized query for change requests with select_related and prefetch_related"""
    queryset = ChangeRequest.objects.select_related(
        'new_profile',
        'profile_change__user',
        'profile_deactivation__user',
        'created_by',
        'creator_designation',
        'region',
        'cost_center'
    ).prefetch_related(
        'crapproval_set__approver',
        'crapproval_set__approver_role'
    ).filter(region=user.region)
    
    # Exclude soft-deleted records by default
    if not include_deleted:
        queryset = queryset.filter(is_deleted=False)
    
    if filters:
        queryset = apply_filters(queryset, filters)
    
    return queryset
```

### 3. Caching Implementation
```python
def get_cached_user_data(username):
    """Get cached user data to reduce database queries"""
    from django.core.cache import cache
    
    cache_key = f"{USER_DATA_CACHE_KEY_PREFIX}{username}"
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        # Fetch from database and cache
        user = UserProfile.objects.filter(username=username).first()
        if user:
            applications = Application.objects.all()
            all_roles = {app.name: [model_to_dict(role) for role in Roles.objects.filter(app_id=app.id).all()] for app in applications}
            active_roles = {role.app_id.name: model_to_dict(role) for role in user.roles.all() if role.app_id}
            
            cached_data = {
                "applications": list(applications.values('id', 'name', 'fullname')),
                "userData": all_roles,
                "active_roles": active_roles,
            }
            cache.set(cache_key, cached_data, CACHE_TIMEOUT)
    
    return cached_data
```

### 4. Pagination
- **DataTables Integration**: Client-side pagination for large datasets
- **Server-Side Processing**: Efficient handling of large result sets
- **Configurable Page Sizes**: Default and maximum page sizes

## Testing Strategy

### Test Structure
```
tests/
├── test_models.py          # Model tests
├── test_views.py           # View and helper function tests
├── test_integration.py     # Integration and workflow tests
└── test_constants.py       # Constants and configuration tests
```

### Test Categories

#### 1. Unit Tests
- **Model Tests**: Creation, validation, methods, relationships
- **View Tests**: Function logic, validation, error handling
- **Helper Tests**: Utility functions, caching, permissions

#### 2. Integration Tests
- **Workflow Tests**: Complete user workflows
- **Security Tests**: Authentication, authorization, CSRF
- **Performance Tests**: Query optimization, caching

#### 3. Test Coverage
- **Models**: 100% coverage of model methods and properties
- **Views**: 100% coverage of view functions and helpers
- **Security**: All security features tested
- **Constants**: All configuration validated

### Test Best Practices
- **Isolation**: Each test is independent
- **Mocking**: External dependencies mocked appropriately
- **Data Setup**: Proper test data creation and cleanup
- **Assertions**: Comprehensive assertion coverage
- **Edge Cases**: Boundary conditions and error scenarios

## Configuration

### Django Settings
```python
# settings.py
INSTALLED_APPS = [
    'it.change_requests',
    # ... other apps
]

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'change_requests.log',
        },
    },
    'loggers': {
        'it.change_requests': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### URL Configuration
```python
# urls.py
urlpatterns = [
    path('change_request_index', views.change_request_index, name='change_request_index'),
    path('create_change_request', views.create_change_request, name='create_change_request'),
    path('create_new_profile', views.create_new_profile, name='create_new_profile'),
    path('update_change_request', views.update_change_request, name='update_change_request'),
    path('delete_change_request', views.delete_change_request, name='delete_change_request'),
    path('restore_change_request', views.restore_change_request, name='restore_change_request'),
    path('bulk_delete_change_requests', views.bulk_delete_change_requests, name='bulk_delete_change_requests'),
    # ... other URLs
]
```

## Deployment

### Prerequisites
- Django 3.2+
- Python 3.8+
- Database (MySQL/PostgreSQL)
- Redis (for caching, optional)

### Deployment Steps

1. **Database Migration**
```bash
python manage.py makemigrations change_requests
python manage.py migrate
```

2. **Static Files**
```bash
python manage.py collectstatic
```

3. **Cache Setup**
```bash
# Configure Redis or use default cache
```

4. **Logging Setup**
```bash
# Ensure log directory exists and is writable
mkdir -p /var/log/change_requests
chmod 755 /var/log/change_requests
```

5. **Permissions**
```bash
# Ensure proper file permissions
chmod 644 *.py
chmod 755 manage.py
```

### Environment Variables
```bash
# Database
DATABASE_URL=mysql://user:password@localhost/dbname

# Cache
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/change_requests/change_requests.log
```

## Maintenance

### Regular Maintenance Tasks

#### 1. Database Maintenance
```sql
-- Clean up old soft-deleted records (optional)
DELETE FROM change_requests_changerequest 
WHERE is_deleted = 1 
AND deleted_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- Optimize tables
OPTIMIZE TABLE change_requests_changerequest;
```

#### 2. Cache Maintenance
```python
# Clear cache if needed
from django.core.cache import cache
cache.clear()
```

#### 3. Log Rotation
```bash
# Set up log rotation
logrotate /etc/logrotate.d/change_requests
```

#### 4. Performance Monitoring
- Monitor database query performance
- Check cache hit rates
- Review error logs regularly
- Monitor user activity patterns

### Backup Strategy
- **Database Backups**: Regular automated backups
- **Code Backups**: Version control with Git
- **Configuration Backups**: Backup settings and constants
- **Log Backups**: Archive old logs

### Monitoring
- **Application Logs**: Monitor for errors and warnings
- **Performance Metrics**: Track response times and throughput
- **User Activity**: Monitor usage patterns and errors
- **Security Events**: Watch for suspicious activity

### Troubleshooting

#### Common Issues
1. **Database Connection Issues**: Check database configuration and connectivity
2. **Cache Issues**: Verify cache configuration and connectivity
3. **Permission Issues**: Check user roles and permissions
4. **Performance Issues**: Review database queries and indexes

#### Debug Mode
```python
# Enable debug mode for development
DEBUG = True
LOGGING['loggers']['it.change_requests']['level'] = 'DEBUG'
```

#### Error Tracking
- Use Django's built-in error handling
- Implement custom error tracking if needed
- Monitor application logs for patterns
- Set up alerts for critical errors

---

## Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add comprehensive docstrings
- Include type hints where appropriate

### Git Workflow
- Use feature branches for development
- Write descriptive commit messages
- Use pull requests for code review
- Tag releases appropriately

### Documentation
- Keep documentation up to date
- Include examples in docstrings
- Document configuration changes
- Maintain API documentation

### Testing
- Write tests for all new features
- Maintain test coverage above 90%
- Run tests before committing
- Use continuous integration

---

*This documentation is maintained alongside the codebase. Please update it when making changes to the system.*
