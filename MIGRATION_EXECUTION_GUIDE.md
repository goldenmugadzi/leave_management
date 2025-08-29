# Knowledge Center Migration Execution Guide

## Overview

This guide provides step-by-step instructions for migrating processes from the Knowledge Center's "PROCESSES AND PROCEDURES" application to the new Process Management system with the enhanced table view interface.

## Prerequisites

### System Requirements
- Django application with both `knowledge_center` and `process_management` apps installed
- Database access with appropriate permissions
- File system access to Knowledge Center uploads directory
- Sufficient storage space for process documents

### Backup Requirements
Before starting the migration, ensure you have:
- Complete database backup
- File system backup of Knowledge Center uploads
- Export of current KC data structure

## Migration Steps

### Step 1: Environment Preparation

#### 1.1 Create Backup
```bash
# Database backup
python manage.py dumpdata knowledge_center > backup_kc_$(date +%Y%m%d).json
python manage.py dumpdata process_management > backup_pm_$(date +%Y%m%d).json

# File system backup (adjust paths as needed)
tar -czf backup_kc_files_$(date +%Y%m%d).tar.gz media/uploads/knowledge_center/
```

#### 1.2 Verify System Health
```bash
# Check database connectivity
python manage.py check

# Verify Knowledge Center data access
python manage.py shell -c "
from knowledge_center.models import FolderApplication
app = FolderApplication.objects.filter(id=2).first()
print(f'KC App: {app.name if app else \"Not found\"}')"

# Check file system permissions
python manage.py shell -c "
import os
from django.conf import settings
upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'processes')
os.makedirs(upload_dir, exist_ok=True)
print('File system permissions OK')"
```

### Step 2: Data Analysis

#### 2.1 Analyze Knowledge Center Structure
```bash
# Basic analysis
python manage.py analyze_kc_structure

# Detailed analysis with file information
python manage.py analyze_kc_structure --detailed

# Export analysis for review
python manage.py analyze_kc_structure --detailed --export=kc_analysis.json
```

#### 2.2 Review Analysis Results
- Check the number of potential processes identified
- Review department distribution
- Identify any data quality issues
- Plan department mappings if needed

### Step 3: Department Setup

#### 3.1 Set Up Process Departments
```bash
# Create standard departments
python manage.py setup_process_departments

# Or create custom departments from file
python manage.py setup_process_departments --export-template=dept_template.json
# Edit dept_template.json as needed
python manage.py setup_process_departments --from-file=dept_template.json
```

#### 3.2 Verify Department Creation
```bash
python manage.py shell -c "
from process_management.models import ProcessDepartment
depts = ProcessDepartment.objects.all().order_by('order')
for dept in depts:
    print(f'{dept.order}: {dept.name}')"
```

### Step 4: Migration Execution

#### 4.1 Dry Run Migration
```bash
# Full dry run
python manage.py migrate_kc_processes --dry-run --verbose

# Dry run for specific department
python manage.py migrate_kc_processes --dry-run --department="Engineering"

# Analysis only (no migration simulation)
python manage.py migrate_kc_processes --analyze-only
```

#### 4.2 Review Dry Run Results
- Check the number of processes to be created
- Review document classifications
- Identify potential issues
- Adjust department mappings if needed

#### 4.3 Execute Migration

##### Option A: Full Migration
```bash
# Full migration with standard settings
python manage.py migrate_kc_processes --batch-size=25 --verbose

# Save results to file
python manage.py migrate_kc_processes --batch-size=25 --output-file=migration_results.json
```

##### Option B: Department-by-Department Migration
```bash
# Migrate each department separately for better control
python manage.py migrate_kc_processes --department="Engineering" --batch-size=10
python manage.py migrate_kc_processes --department="Commercial Operations" --batch-size=10
python manage.py migrate_kc_processes --department="Finance" --batch-size=10
# Continue for each department...
```

##### Option C: Resume Failed Migration
```bash
# If migration fails, resume from checkpoint
python manage.py migrate_kc_processes --resume=migration_20241201_143022_abc12345
```

### Step 5: Post-Migration Verification

#### 5.1 Verify Migration Results
```bash
# Check process counts
python manage.py shell -c "
from process_management.models import Process, ProcessDocument, ProcessDepartment
print(f'Departments: {ProcessDepartment.objects.count()}')
print(f'Processes: {Process.objects.count()}')
print(f'Documents: {ProcessDocument.objects.count()}')
print(f'Active Documents: {ProcessDocument.objects.filter(is_active=True).count()}')"

# Check document accessibility
python manage.py shell -c "
from process_management.models import ProcessDocument
docs = ProcessDocument.objects.filter(is_active=True)
accessible = sum(1 for doc in docs if doc.file and doc.file.name)
print(f'Documents with files: {accessible}/{docs.count()}')"
```

#### 5.2 Test Table View Interface
1. Navigate to Process Management in the web interface
2. Verify table view is working correctly
3. Test search and filtering functionality
4. Test document downloads
5. Verify department view still works

#### 5.3 Spot Check Data Quality
```bash
# Check for processes without documents
python manage.py shell -c "
from process_management.models import Process
processes_without_docs = Process.objects.filter(documents__isnull=True)
print(f'Processes without documents: {processes_without_docs.count()}')"

# Check for duplicate process names
python manage.py shell -c "
from process_management.models import Process
from django.db.models import Count
duplicates = Process.objects.values('name').annotate(
    count=Count('name')).filter(count__gt=1)
print(f'Duplicate process names: {duplicates.count()}')"
```

### Step 6: Data Cleanup and Optimization

#### 6.1 Archive Migrated KC Data (Optional)
```bash
# Mark migrated KC files as archived
python manage.py shell -c "
from knowledge_center.models import KnowldgeCentreFile, FolderApplication
from process_management.models import ProcessDocument

# Get migrated file IDs from process documents
migrated_ids = set()
for doc in ProcessDocument.objects.filter(metadata__migrated_from_kc=True):
    if 'original_kc_file_id' in doc.metadata:
        migrated_ids.add(doc.metadata['original_kc_file_id'])

# Archive migrated files
pp_app = FolderApplication.objects.filter(id=2).first()
if pp_app:
    archived_count = KnowldgeCentreFile.objects.filter(
        id__in=migrated_ids,
        folder__folder_application=pp_app
    ).update(archived=True)
    print(f'Archived {archived_count} KC files')
"
```

#### 6.2 Update Database Indexes
```bash
# Run database optimization
python manage.py migrate
python manage.py collectstatic --noinput
```

### Step 7: User Communication and Training

#### 7.1 Prepare User Communication
- Create announcement about new table view interface
- Prepare user guide updates
- Schedule training sessions
- Set up feedback collection

#### 7.2 Monitor System Performance
- Monitor database performance
- Check file access patterns
- Monitor user adoption
- Collect user feedback

## Troubleshooting

### Common Issues and Solutions

#### Issue: Migration Fails with Database Errors
**Solution:**
```bash
# Check database constraints
python manage.py check
# Resume from last checkpoint
python manage.py migrate_kc_processes --resume=MIGRATION_ID
```

#### Issue: File Access Errors
**Solution:**
```bash
# Check file permissions
ls -la media/uploads/
# Verify file paths in KC data
python manage.py shell -c "
from knowledge_center.models import KnowldgeCentreFile
files = KnowldgeCentreFile.objects.filter(archived=False)[:10]
for f in files:
    print(f'{f.filename}: {f.file.name if f.file else \"No file\"}')"
```

#### Issue: Document Classification Problems
**Solution:**
- Review document type patterns in `knowledge_center_migrator.py`
- Adjust classification rules
- Re-run migration with updated patterns

#### Issue: Department Mapping Issues
**Solution:**
- Review department mapping in `ProcessCandidateAnalyzer.DEPARTMENT_MAPPING`
- Create custom department mappings
- Update departments and re-run migration

### Recovery Procedures

#### Rollback Migration
```bash
# Restore from backup
python manage.py flush --noinput
python manage.py loaddata backup_pm_YYYYMMDD.json

# Restore file system
rm -rf media/uploads/processes/
tar -xzf backup_kc_files_YYYYMMDD.tar.gz
```

#### Partial Rollback
```bash
# Delete only migrated processes
python manage.py shell -c "
from process_management.models import Process, ProcessDocument
# Delete processes created during migration
migrated_processes = Process.objects.filter(
    documents__metadata__migrated_from_kc=True
).distinct()
count = migrated_processes.count()
migrated_processes.delete()
print(f'Deleted {count} migrated processes')
"
```

## Performance Considerations

### Batch Size Optimization
- Start with small batch sizes (10-25) for initial testing
- Increase batch size (50-100) for production migration
- Monitor memory usage and database performance

### Migration Timing
- Run migration during off-peak hours
- Consider maintenance window for large migrations
- Plan for potential system slowdown during migration

### Resource Monitoring
```bash
# Monitor during migration
watch -n 5 'python manage.py shell -c "
from process_management.models import Process, ProcessDocument
print(f\"Processes: {Process.objects.count()}\")
print(f\"Documents: {ProcessDocument.objects.count()}\")
"'
```

## Success Criteria

### Technical Success Metrics
- [ ] Migration completion rate > 95%
- [ ] Data integrity verification passes
- [ ] File accessibility rate > 98%
- [ ] No critical errors in migration log
- [ ] Table view interface fully functional

### User Success Metrics
- [ ] User can access all migrated processes
- [ ] Document downloads work correctly
- [ ] Search and filtering functions properly
- [ ] Performance meets user expectations
- [ ] User feedback is positive

## Post-Migration Tasks

### Immediate (Day 1)
- [ ] Verify all systems operational
- [ ] Monitor error logs
- [ ] Respond to user issues
- [ ] Collect initial feedback

### Short-term (Week 1)
- [ ] Analyze usage patterns
- [ ] Address any data quality issues
- [ ] Optimize performance if needed
- [ ] Update documentation

### Long-term (Month 1)
- [ ] Evaluate migration success
- [ ] Plan Knowledge Center decommissioning
- [ ] Implement user feedback
- [ ] Plan future enhancements

## Conclusion

This migration will provide users with the Excel-like table interface they requested while maintaining all existing functionality. The phased approach and comprehensive error handling ensure a smooth transition with minimal disruption to daily operations.

For questions or issues during migration, refer to the troubleshooting section or contact the system administrator.