# Design Document

## Overview

This design document outlines the architecture and implementation approach for enhancing the executive dashboard with three new data sections: Weekly Collections (replacing Sales), Weekly Revenue Lost (replacing Power Outages), and Debtors with category-based breakdowns. The solution maintains the existing Django-based architecture while adding new models, API endpoints, and inline editing capabilities.

## Architecture

### High-Level Architecture

The dashboard enhancement follows the existing MVC pattern:

```
Frontend (Templates/JavaScript) 
    ↓ AJAX Requests
API Layer (Django Views)
    ↓ ORM Queries  
Data Layer (Django Models)
    ↓ Database Operations
PostgreSQL Database
```

### Component Integration

The new features integrate with existing components:

- **Models**: Extend `executive/general_dashboards/models.py` with new data models
- **Views**: Add new API endpoints to `executive/general_dashboards/views.py`
- **Templates**: Update dashboard template with new sections
- **JavaScript**: Add inline editing functionality and AJAX handlers
- **Admin**: Register new models for administrative management

## Components and Interfaces

### 1. Data Models

#### WeeklyCollections Model
```python
class WeeklyCollections(models.Model):
    week = models.CharField(max_length=20)
    zwl_millions = models.DecimalField(max_digits=10, decimal_places=2)
    usd_millions = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Location-based filtering (consistent with existing models)
    region = models.ForeignKey('it.users.Regions', on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey('it.users.Districts', on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey('it.users.Depots', on_delete=models.CASCADE, null=True, blank=True)
    
    # Time tracking
    year = models.IntegerField(default=2025)
    week_number = models.IntegerField()
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('it.users.UserProfile', on_delete=models.SET_NULL, null=True)
```

#### WeeklyRevenueLost Model
```python
class WeeklyRevenueLost(models.Model):
    week = models.CharField(max_length=20)
    faults_mwh = models.DecimalField(max_digits=10, decimal_places=2)
    maintenance_mwh = models.DecimalField(max_digits=10, decimal_places=2)
    total_mwh = models.DecimalField(max_digits=10, decimal_places=2)  # Auto-calculated
    
    # Location and time fields (same pattern as WeeklyCollections)
    # Audit fields (same pattern as WeeklyCollections)
```

#### DebtorCategory Model
```python
class DebtorCategory(models.Model):
    CATEGORY_CHOICES = [
        ('mining', 'Mining'),
        ('domestic', 'Domestic'),
        ('industry', 'Industry'),
        ('commercial', 'Commercial'),
        ('farming', 'Farming'),
        ('government', 'Government'),
        ('parastatal', 'Parastatal'),
        ('local_authority', 'Local Authority'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # 0.00 to 100.00
    
    # Location and audit fields (same pattern)
```

### 2. API Endpoints

#### Data Retrieval Endpoints
- `GET /executive/general_dashboards/weekly-collections/` - Get collections data
- `GET /executive/general_dashboards/weekly-revenue-lost/` - Get revenue lost data  
- `GET /executive/general_dashboards/debtors/` - Get debtor categories data

#### Inline Editing Endpoints
- `POST /executive/general_dashboards/weekly-collections/update/` - Update collections data
- `POST /executive/general_dashboards/weekly-revenue-lost/update/` - Update revenue lost data
- `POST /executive/general_dashboards/debtors/update/` - Update debtor percentages

#### Filter Endpoints
- `GET /executive/general_dashboards/data/?region=X&district=Y&depot=Z` - Filtered data

### 3. Frontend Components

#### Dashboard Sections Structure
```html
<!-- Weekly Collections Section -->
<div class="dashboard-section" id="weekly-collections">
    <h3>Weekly Collections</h3>
    <table class="editable-table">
        <thead>
            <tr>
                <th>Week</th>
                <th>ZWL (Millions)</th>
                <th>USD (Millions)</th>
            </tr>
        </thead>
        <tbody id="collections-data">
            <!-- Dynamic content -->
        </tbody>
    </table>
</div>

<!-- Weekly Revenue Lost Section -->
<div class="dashboard-section" id="weekly-revenue-lost">
    <h3>Weekly Revenue Lost</h3>
    <table class="editable-table">
        <thead>
            <tr>
                <th>Week</th>
                <th>Faults (MWh)</th>
                <th>Maintenance (MWh)</th>
                <th>Total (MWh)</th>
            </tr>
        </thead>
        <tbody id="revenue-lost-data">
            <!-- Dynamic content -->
        </tbody>
    </table>
</div>

<!-- Debtors Section -->
<div class="dashboard-section" id="debtors">
    <h3>Debtors</h3>
    <table class="editable-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Category</th>
                <th>Percentage (%)</th>
            </tr>
        </thead>
        <tbody id="debtors-data">
            <!-- Dynamic content -->
        </tbody>
    </table>
</div>
```

#### Inline Editing Component
```javascript
class InlineEditor {
    constructor(tableSelector, apiEndpoint) {
        this.table = document.querySelector(tableSelector);
        this.apiEndpoint = apiEndpoint;
        this.initializeEditing();
    }
    
    initializeEditing() {
        // Add click handlers for editable cells
        // Convert cells to input fields on click
        // Handle save/cancel operations
        // Validate data before saving
        // Update UI with success/error feedback
    }
    
    async saveData(rowId, field, value) {
        // AJAX call to save data
        // Handle response and update UI
    }
}
```

### 4. Data Validation and Business Logic

#### Collections Data Validation
- ZWL and USD values must be non-negative decimals
- Values are stored in millions (e.g., 5.2 represents 5.2 million)
- Week format validation (e.g., "Week 1", "Week 2")

#### Revenue Lost Data Validation  
- Faults and maintenance MWh must be non-negative
- Total MWh is automatically calculated as faults + maintenance
- Cannot manually edit total field

#### Debtor Percentage Validation
- All percentages must be between 0.00 and 100.00
- Sum of all category percentages must equal 100.00
- Auto-adjustment logic when one percentage changes

## Data Models

### Database Schema Changes

#### New Tables
1. `general_dashboards_weeklycollections`
2. `general_dashboards_weeklyrevenuelost` 
3. `general_dashboards_debtorcategory`

#### Migration Strategy
- Create new models alongside existing ones
- Populate with initial/sample data
- Update views to use new models
- Remove old model references (WeeklySales, WeeklyOutage)

### Data Relationships
- All models follow the same location-based filtering pattern as existing models
- Foreign key relationships to Regions, Districts, Depots tables
- Audit trail relationships to UserProfile for tracking changes

## Error Handling

### Frontend Error Handling
- **Validation Errors**: Display inline error messages next to invalid fields
- **Network Errors**: Show toast notifications for connection issues
- **Permission Errors**: Display appropriate access denied messages
- **Data Conflicts**: Handle concurrent editing scenarios

### Backend Error Handling
- **Data Validation**: Return structured error responses with field-specific messages
- **Database Errors**: Log errors and return generic user-friendly messages
- **Permission Checks**: Validate user permissions before allowing edits
- **Transaction Management**: Use database transactions for data consistency

### Error Response Format
```json
{
    "success": false,
    "errors": {
        "field_name": ["Error message 1", "Error message 2"],
        "non_field_errors": ["General error message"]
    },
    "message": "User-friendly error description"
}
```

## Testing Strategy

### Unit Tests
- **Model Tests**: Validate model constraints, calculations, and relationships
- **View Tests**: Test API endpoints with various input scenarios
- **Validation Tests**: Test data validation logic and error handling
- **Permission Tests**: Verify access control for different user roles

### Integration Tests
- **End-to-End Editing**: Test complete inline editing workflow
- **Filter Integration**: Test location-based filtering across all sections
- **Data Consistency**: Test automatic calculations and percentage adjustments
- **Concurrent Access**: Test multiple users editing simultaneously

### Frontend Tests
- **JavaScript Unit Tests**: Test inline editing components
- **UI Interaction Tests**: Test user interface responsiveness
- **AJAX Tests**: Mock API calls and test error handling
- **Cross-browser Tests**: Ensure compatibility across browsers

### Test Data Management
- **Fixtures**: Create test data fixtures for consistent testing
- **Factory Classes**: Use factory pattern for generating test data
- **Database Isolation**: Ensure tests don't interfere with each other
- **Performance Tests**: Test with large datasets to ensure scalability

### Testing Tools
- **Django TestCase**: For backend unit and integration tests
- **Django REST Framework Test Client**: For API endpoint testing
- **Jest/Jasmine**: For JavaScript unit tests
- **Selenium**: For end-to-end browser testing
- **Coverage.py**: For test coverage reporting

## Security Considerations

### Authentication and Authorization
- Reuse existing user authentication system
- Implement role-based permissions for editing capabilities
- Validate user permissions on every API call

### Data Validation
- Server-side validation for all input data
- SQL injection prevention through ORM usage
- XSS prevention through proper template escaping

### Audit Trail
- Track all data changes with user and timestamp information
- Log sensitive operations for security monitoring
- Maintain data integrity through database constraints

## Performance Considerations

### Database Optimization
- Add appropriate indexes for location-based filtering
- Use database-level constraints for data validation
- Implement efficient queries for dashboard data retrieval

### Frontend Optimization
- Lazy loading for large datasets
- Debounced input handling for inline editing
- Efficient DOM manipulation for table updates

### Caching Strategy
- Cache dashboard data for improved response times
- Implement cache invalidation on data updates
- Use browser caching for static assets