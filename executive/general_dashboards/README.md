# General Dashboards Module

A comprehensive executive dashboard system for monitoring business performance metrics, financial data, and operational KPIs.

## Overview

The General Dashboards module provides real-time monitoring and analysis of key business metrics through an interactive web interface. It features location-based filtering, inline editing capabilities, and responsive design for both desktop and mobile devices.

## Features

### 🎯 **Core Dashboard Components**
- **Metric Cards**: Visual representation of key performance indicators
- **Weekly Collections**: Financial data tracking in ZWL and USD currencies
- **Weekly Revenue Lost**: Monitoring of revenue losses due to faults and maintenance
- **Debtor Categories**: Customer debt classification with percentage breakdowns

### 🔧 **Interactive Features**
- **Inline Editing**: Click-to-edit functionality for real-time data updates
- **Location Filtering**: Hierarchical filtering by Region → District → Depot
- **Real-time Updates**: HTMX-powered dynamic content updates
- **Responsive Design**: Mobile-first approach with modern UI/UX

### 📊 **Data Management**
- **CRUD Operations**: Full create, read, update, delete functionality
- **Data Validation**: Comprehensive input validation and error handling
- **Audit Trail**: Track changes with user attribution and timestamps
- **Sample Data**: Built-in sample data generation for testing

## Architecture

### Models

#### WeeklyCollections
Tracks weekly financial collections in both ZWL and USD currencies.

```python
class WeeklyCollections(models.Model):
    week = models.CharField(max_length=20)
    zwl_millions = models.DecimalField(max_digits=10, decimal_places=2)
    usd_millions = models.DecimalField(max_digits=10, decimal_places=2)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE)
    year = models.IntegerField()
    week_number = models.IntegerField()
    # ... audit fields
```

#### WeeklyRevenueLost
Monitors revenue losses categorized by faults and maintenance.

```python
class WeeklyRevenueLost(models.Model):
    week = models.CharField(max_length=20)
    faults_mwh = models.DecimalField(max_digits=10, decimal_places=2)
    maintenance_mwh = models.DecimalField(max_digits=10, decimal_places=2)
    total_mwh = models.DecimalField(max_digits=10, decimal_places=2)  # Auto-calculated
    # ... location and time fields
```

#### DebtorCategory
Customer debt classification with percentage breakdowns.

```python
class DebtorCategory(models.Model):
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    # ... location and time fields
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboards/` | GET | Main dashboard page |
| `/dashboards/dashboard-data/` | GET | Retrieve dashboard data with optional filters |
| `/dashboards/save-dashboard-data/` | POST | Save edited dashboard data |
| `/dashboards/regions/` | GET | Get location hierarchy for filtering |
| `/dashboards/user-permissions/` | GET | Get user access permissions |
| `/dashboards/create-sample-data/` | POST | Generate sample data for testing |

### Views

- **`dashboard_index`**: Main dashboard page rendering
- **`get_dashboard_data`**: API endpoint for dashboard data retrieval
- **`save_dashboard_data`**: API endpoint for data updates
- **`get_regions`**: Location data for filtering
- **`get_user_permissions`**: User access control
- **`create_sample_data`**: Sample data generation

## Installation & Setup

### 1. Prerequisites
- Django 4.0+
- Django REST Framework
- HTMX (included via CDN)
- PostgreSQL/MySQL database

### 2. Installation
```bash
# The module is already included in the project
# Ensure it's in INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    # ...
    'executive.general_dashboards.apps.GeneralDashboardsConfig',
    # ...
]
```

### 3. Database Setup
```bash
# Run migrations
python manage.py makemigrations general_dashboards
python manage.py migrate

# Create sample data (optional)
python manage.py create_sample_dashboard_data
```

### 4. URL Configuration
```python
# In main urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path('dashboards/', include('executive.general_dashboards.urls')),
    # ...
]
```

## Usage

### Accessing the Dashboard

1. Navigate to `/dashboards/` in your browser
2. The dashboard will automatically load with current data
3. Use the location filters to narrow down data by region/district/depot

### Editing Data

1. **Click on any editable cell** (highlighted with hover effects)
2. **Enter new value** in the input field
3. **Click ✓ to save** or ✗ to cancel
4. **Data is automatically validated** and saved to the database

### Location Filtering

1. **Select Region** from the dropdown
2. **Select District** (populated based on region selection)
3. **Select Depot** (populated based on district selection)
4. **Data updates automatically** based on your selections

### Data Validation

- **Percentages**: Must be between 0-100% and total ≤100% for same location/time
- **Currency Values**: Must be non-negative numbers
- **MWh Values**: Must be non-negative numbers
- **Week Format**: Must follow "Week X" pattern

## Configuration

### Settings

The module uses standard Django settings. Key configurations:

```python
# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        # ... other settings
    }
}

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Customization

#### Styling
- CSS classes are defined in `static/assets/css/dashboard_sections.css`
- Responsive breakpoints: 480px (mobile), 768px (tablet), 1024px (desktop)
- Color schemes can be customized via CSS variables

#### Data Sources
- Models can be extended to include additional fields
- New dashboard sections can be added by extending the views
- Custom metrics can be implemented in the `get_dashboard_data` view

## Testing

### Running Tests
```bash
# Run all tests
python manage.py test executive.general_dashboards.tests

# Run specific test classes
python manage.py test executive.general_dashboards.tests.ModelsTestCase
python manage.py test executive.general_dashboards.tests.ViewsTestCase

# Run with coverage
coverage run --source='.' manage.py test executive.general_dashboards.tests
coverage report
```

### Test Coverage

The test suite covers:
- **Models**: CRUD operations, validation, constraints
- **Views**: API endpoints, authentication, permissions
- **Serializers**: Data validation, field mapping
- **Integration**: HTMX functionality, filtering, editing
- **Security**: Authentication, authorization, input validation
- **Performance**: Large datasets, concurrent operations
- **Edge Cases**: Empty data, invalid inputs, boundary values

## Performance Considerations

### Database Optimization
- **Indexes**: Added on frequently queried fields (year, week_number, location)
- **Queries**: Optimized with select_related for location data
- **Filtering**: Efficient location-based filtering with Q objects

### Frontend Performance
- **HTMX**: Minimal JavaScript for dynamic updates
- **Lazy Loading**: Data loaded on-demand based on filters
- **Caching**: Consider implementing Redis caching for large datasets

### Scalability
- **Pagination**: Can be added for very large datasets
- **Background Tasks**: Consider Celery for data processing
- **CDN**: Static assets can be served via CDN

## Security Features

### Authentication & Authorization
- **Session-based authentication** for web interface
- **Token authentication** for API endpoints
- **Permission-based access control** for editing capabilities

### Data Validation
- **Input sanitization** to prevent XSS attacks
- **SQL injection protection** via Django ORM
- **CSRF protection** enabled for all forms

### Audit Trail
- **User attribution** for all data changes
- **Timestamp tracking** for creation and updates
- **Change logging** for compliance requirements

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
1. Check database migrations: `python manage.py showmigrations general_dashboards`
2. Verify sample data exists: `python manage.py create_sample_dashboard_data`
3. Check browser console for JavaScript errors

#### Editing Not Working
1. Verify user authentication and permissions
2. Check CSRF token in browser cookies
3. Ensure HTMX is loading correctly

#### Location Filters Not Working
1. Verify location data exists in the database
2. Check API endpoint responses
3. Ensure JavaScript is enabled in the browser

#### Performance Issues
1. Check database query performance
2. Verify indexes are properly created
3. Consider implementing caching for large datasets

### Debug Mode

Enable Django debug mode for detailed error information:

```python
DEBUG = True
```

### Logging

The module includes comprehensive logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'executive.general_dashboards': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Add docstrings for all public methods
- Include type hints where appropriate

### Testing Guidelines
- Maintain test coverage above 90%
- Test both positive and negative scenarios
- Include performance tests for new features
- Test edge cases and error conditions

## Roadmap

### Planned Features
- **Advanced Analytics**: Trend analysis and forecasting
- **Export Functionality**: PDF/Excel report generation
- **Real-time Updates**: WebSocket integration for live data
- **Mobile App**: Native mobile application
- **Advanced Filtering**: Date ranges, custom metrics
- **Dashboard Builder**: Drag-and-drop dashboard customization

### Performance Improvements
- **Database Optimization**: Query optimization and indexing
- **Caching Strategy**: Redis integration for better performance
- **CDN Integration**: Global content delivery
- **Background Processing**: Async data processing with Celery

## Support

### Documentation
- This README file
- Django admin interface for data management
- API documentation via Django REST Framework

### Issues
- Report bugs via GitHub issues
- Include error logs and reproduction steps
- Provide environment details (Django version, database, etc.)

### Community
- Django community forums
- Stack Overflow with appropriate tags
- Project-specific discussions

## License

This module is part of the BEII v1 project and follows the project's licensing terms.

## Changelog

### Version 1.0.0 (Current)
- Initial release with core dashboard functionality
- Weekly collections and revenue tracking
- Debtor categorization system
- Location-based filtering
- Inline editing capabilities
- Responsive design implementation
- Comprehensive test coverage
- Security and performance optimizations

---

**Note**: This module is designed to be production-ready and includes comprehensive testing, security features, and performance optimizations. For production deployment, ensure proper environment configuration and consider implementing additional monitoring and logging solutions.
