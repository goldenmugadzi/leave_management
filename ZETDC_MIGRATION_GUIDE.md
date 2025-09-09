# ZETDC Knowledge Center Migration Guide

## Overview

This guide is specifically tailored for migrating ZETDC's processes from the Knowledge Center to the new Process Management system. Based on your current structure, you have:

### Current Structure Analysis

#### Applications Available:
1. **ID 1**: "KNOWLEDGE CENTRE" - General knowledge content
2. **ID 2**: "PROCESS MAPS" - Process-related content

#### Process Organization (from your images):
Your processes are organized into these main categories:

**Main Process Areas:**
- **PROCESSES INTERACTIONS** - Process flow diagrams and interactions
- **PROCESS MAPS** - Visual process maps and flowcharts  
- **PROCEDURES AND WORK INSTRUCTIONS** - Detailed procedures
- **PROCESS FORMS** - Process-related forms and templates
- **REGISTERS** - Risk registers and other process registers
- **CONTEXT OF THE ORGANISATION** - Organizational context documents

**Departmental Structure:**
- Commercial Operations
- Engineering  
- Management Processes
- Information Communication Technology
- Finance
- Human Resources
- Risk Management
- Procurement
- Stakeholder Relations
- Legal Services

## Migration Strategy for ZETDC

### Phase 1: Pre-Migration Setup

#### Step 1: List Available Applications
```bash
python manage.py list_kc_applications
```

This will show you all available KC applications and help confirm which one contains your processes.

#### Step 2: Analyze Your Current Structure
```bash
# Analyze the PROCESS MAPS application (ID 2)
python manage.py analyze_kc_structure --app-id=2 --detailed

# If processes are in KNOWLEDGE CENTRE (ID 1), analyze that instead
python manage.py analyze_kc_structure --app-id=1 --detailed
```

#### Step 3: Set Up Departments
```bash
# Create departments matching your organizational structure
python manage.py setup_process_departments
```

This will create departments matching your structure:
- Commercial Operations
- Engineering
- Management Processes
- Information Communication Technology
- Finance
- Human Resources
- Risk Management
- Procurement
- Stakeholder Relations
- Legal Services

### Phase 2: Test Migration

#### Step 1: Test Migration Logic
```bash
# Test with your specific application ID
python manage.py test_kc_migration --app-id=2 --show-details

# If your processes are in application ID 1:
python manage.py test_kc_migration --app-id=1 --show-details
```

#### Step 2: Dry Run Migration
```bash
# Dry run for PROCESS MAPS application
python manage.py migrate_kc_processes --app-id=2 --dry-run --verbose

# Or for KNOWLEDGE CENTRE application
python manage.py migrate_kc_processes --app-id=1 --dry-run --verbose
```

### Phase 3: Execute Migration

#### Option A: Full Migration
```bash
# Migrate all processes from the correct application
python manage.py migrate_kc_processes --app-id=2 --batch-size=20 --verbose

# Save results for review
python manage.py migrate_kc_processes --app-id=2 --batch-size=20 --output-file=zetdc_migration_results.json
```

#### Option B: Selective Migration by Folder
If you want to migrate specific folders first:

```bash
# Migrate specific department processes
python manage.py migrate_kc_processes --app-id=2 --department="Engineering" --batch-size=10
python manage.py migrate_kc_processes --app-id=2 --department="Commercial Operations" --batch-size=10
```

### Phase 4: Verification

#### Step 1: Check Migration Results
```bash
# Verify processes were created
python manage.py shell -c "
from process_management.models import Process, ProcessDocument, ProcessDepartment
print(f'Departments: {ProcessDepartment.objects.count()}')
print(f'Processes: {Process.objects.count()}')
print(f'Documents: {ProcessDocument.objects.count()}')

# Show processes by department
for dept in ProcessDepartment.objects.all():
    count = Process.objects.filter(department=dept).count()
    print(f'{dept.name}: {count} processes')
"
```

#### Step 2: Test New Interface
1. Navigate to Process Management in your web interface
2. Verify the table view shows your processes
3. Test the search functionality
4. Try downloading some documents
5. Verify the department filters work

## Expected Results for ZETDC

Based on your folder structure, the migration should:

### Document Classification
- **Process Maps**: Files from "PROCESS MAPS" and "PROCESSES INTERACTIONS" folders
- **Procedures**: Files from "PROCEDURES AND WORK INSTRUCTIONS" folder
- **Risk Registers**: Files from "REGISTERS" folder
- **Forms**: Files from "PROCESS FORMS" folder (classified as procedures)

### Department Mapping
Your folders will be mapped to departments as follows:
- Commercial-related folders → Commercial Operations
- Engineering-related folders → Engineering
- Management/Executive folders → Management Processes
- ICT/IT folders → Information Communication Technology
- Finance folders → Finance
- HR folders → Human Resources
- Risk folders → Risk Management
- Procurement folders → Procurement
- Legal folders → Legal Services

### Process Organization
Each process will be created with:
- **Name**: Extracted from folder/file names
- **Department**: Based on folder hierarchy and content
- **Documents**: Classified by type and linked to the process
- **Metadata**: Original KC folder information preserved

## Troubleshooting for ZETDC

### Issue: No Processes Found
If the migration finds no processes:

1. **Check the correct application ID**:
   ```bash
   python manage.py list_kc_applications
   ```

2. **Try the other application**:
   ```bash
   python manage.py analyze_kc_structure --app-id=1 --detailed
   ```

3. **Check folder structure**:
   Look for folders that contain actual files, not just subfolders.

### Issue: Wrong Department Assignments
If processes are assigned to wrong departments:

1. **Review department mapping** in `knowledge_center_migrator.py`
2. **Update the DEPARTMENT_MAPPING** dictionary
3. **Re-run migration** after updates

### Issue: Document Classification Problems
If documents are not classified correctly:

1. **Check document filenames** - ensure they contain keywords like "map", "procedure", "register"
2. **Update DOCUMENT_TYPE_PATTERNS** in the migrator
3. **Re-run migration** with updated patterns

## Post-Migration for ZETDC

### User Training
1. **Show users the new table view** - emphasize the Excel-like interface
2. **Demonstrate search functionality** - show how to find processes quickly
3. **Train on document downloads** - direct access from table view
4. **Explain department organization** - how processes are now organized

### System Optimization
1. **Monitor performance** - ensure the new system performs well
2. **Collect user feedback** - gather input on the new interface
3. **Plan Knowledge Center transition** - decide when to phase out old system

### Success Metrics for ZETDC
- All process folders successfully migrated
- Documents properly classified and accessible
- Users can find processes faster than before
- Download functionality works for all document types
- Department organization matches your business structure

## Support

If you encounter issues during migration:

1. **Check the migration logs** for detailed error information
2. **Use the resume functionality** if migration fails partway through
3. **Contact system administrator** with specific error messages
4. **Review this guide** for troubleshooting steps

The migration is designed to preserve all your existing process organization while providing the improved table-based interface your users requested.