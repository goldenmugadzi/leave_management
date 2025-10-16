# Equipment Type Implementation for Substation Inspections

## Overview

The substation inspection system now supports **equipment type categorization** to better organize and manage different types of inspection checklists. This allows for more granular filtering and management of inspection items based on the specific equipment being inspected.

## Equipment Types Supported

### 1. **Substation** (`substation`)
- **Purpose**: General substation infrastructure and facility inspections
- **Items**: 21 checklist items covering security, environmental, electrical, mechanical, and documentation
- **Examples**: Perimeter fencing, access roads, lighting, firefighting equipment, battery banks

### 2. **Transformer** (`transformer`)
- **Purpose**: Transformer-specific electrical and mechanical inspections
- **Items**: 21 checklist items focused on electrical equipment and measurements
- **Examples**: Oil levels, temperature gauges, tap changers, CTs/VTs, cooling systems

### 3. **Circuit Breaker** (`circuit_breaker`)
- **Purpose**: Circuit breaker equipment inspections
- **Items**: 19 checklist items covering electrical and mechanical components
- **Examples**: CB make/type, counter readings, oil levels, SF6 gas, relay systems

### 4. **Additional Equipment Types** (Available for future use)
- **Switchgear** (`switchgear`)
- **Protection Equipment** (`protection`)
- **Auxiliary Equipment** (`auxiliary`)
- **General** (`general`)

## Implementation Details

### Database Schema
```python
class InspectionChecklistItem(models.Model):
    EQUIPMENT_TYPE_CHOICES = [
        ('substation', 'Substation'),
        ('transformer', 'Transformer'),
        ('circuit_breaker', 'Circuit Breaker'),
        ('switchgear', 'Switchgear'),
        ('protection', 'Protection Equipment'),
        ('auxiliary', 'Auxiliary Equipment'),
        ('general', 'General'),
    ]
    
    equipment_type = models.CharField(
        max_length=20, 
        choices=EQUIPMENT_TYPE_CHOICES, 
        default='general'
    )
    # ... other fields
```

### Item Code Prefixes
- **SUB-**: Substation items (e.g., `SUB-001`, `SUB-002`)
- **TRF-**: Transformer items (e.g., `TRF-001`, `TRF-002`)
- **CB-**: Circuit Breaker items (e.g., `CB-001`, `CB-002`)

### CSV Data Structure
```csv
item_code,title,description,equipment_type,category,severity,is_mandatory,is_active,reference_standard,frequency
SUB-001,Perimeter wall/fencing,Check perimeter wall and fencing for integrity and security,substation,security,medium,true,true,IEEE 141,monthly
TRF-001,Tap changer counter reading,Record tap changer counter reading,transformer,electrical,medium,true,true,IEEE 141,monthly
CB-001,CB Make,Record circuit breaker manufacturer and model,circuit_breaker,documentation,medium,true,true,IEEE 141,monthly
```

## Usage Examples

### Loading Data
```bash
# Load all equipment types
python manage.py load_checklist_items

# Load specific equipment type
python manage.py load_checklist_items --file substation
python manage.py load_checklist_items --file transformer
python manage.py load_checklist_items --file circuit_breaker

# Clear existing and reload all
python manage.py load_checklist_items --clear
```

### Filtering in Code
```python
# Get all substation items
substation_items = InspectionChecklistItem.objects.filter(
    equipment_type='substation'
)

# Get all transformer items
transformer_items = InspectionChecklistItem.objects.filter(
    equipment_type='transformer'
)

# Get all circuit breaker items
cb_items = InspectionChecklistItem.objects.filter(
    equipment_type='circuit_breaker'
)

# Get high severity electrical items across all equipment types
critical_electrical = InspectionChecklistItem.objects.filter(
    category='electrical',
    severity='high'
)

# Get items by equipment type and category
substation_electrical = InspectionChecklistItem.objects.filter(
    equipment_type='substation',
    category='electrical'
)
```

### Admin Interface
- **List Display**: Shows equipment_type column
- **Filters**: Filter by equipment_type, category, severity, etc.
- **Search**: Search across item codes, titles, descriptions
- **Grouping**: Items are ordered by equipment_type, then category, then item_code

### Web Interface
- **Filtering**: Users can filter checklist items by equipment type
- **Search**: Search across all fields including equipment type
- **Grouping**: Items are displayed grouped by equipment type

## Benefits

### 1. **Better Organization**
- Clear separation of different equipment inspection types
- Easier to find and manage specific inspection items
- Logical grouping in admin and web interfaces

### 2. **Flexible Filtering**
- Filter by equipment type, category, severity, or any combination
- Easy to create equipment-specific inspection reports
- Support for mixed equipment inspections

### 3. **Scalability**
- Easy to add new equipment types
- Consistent structure for all equipment types
- Future-proof design for additional equipment

### 4. **Maintenance**
- Equipment-specific maintenance schedules
- Targeted inspection procedures
- Specialized reporting by equipment type

## File Structure

```
substation_inspections/
├── data/
│   ├── monthly_substation_checklist_items.csv
│   ├── monthly_transformer_checklist_items.csv
│   ├── monthly_circuit_breaker_checklist_items.csv
│   ├── CHECKLIST_ITEMS_EXPLANATION.md
│   └── EQUIPMENT_TYPE_IMPLEMENTATION.md
├── management/
│   └── commands/
│       └── load_checklist_items.py
├── models.py (updated with equipment_type field)
├── forms.py (updated with equipment_type support)
├── views.py (updated with equipment_type filtering)
└── admin.py (updated with equipment_type display)
```

## Migration

To apply the equipment_type field to existing installations:

```bash
# Create migration
python manage.py makemigrations substation_inspections

# Apply migration
python manage.py migrate substation_inspections

# Load checklist items
python manage.py load_checklist_items
```

## Future Enhancements

1. **Equipment-Specific Templates**: Pre-configured checklists for different equipment configurations
2. **Conditional Items**: Items that appear based on equipment type or configuration
3. **Equipment Integration**: Link checklist items to specific equipment records
4. **Dynamic Severity**: Severity levels that adjust based on equipment age or condition
5. **Equipment-Specific Reporting**: Specialized reports for different equipment types
