# Process Management System - User Guide

## Overview

The Process Management System provides a modern, relational approach to organizing and accessing organizational processes. It replaces the folder-based system with a structured departmental view that makes finding and managing processes much easier.

## Features

### For All Users

#### 1. Process Navigation
- **Departmental View**: Processes are organized by 11 main departments
- **Process Counts**: Each department shows how many processes it contains
- **Search Functionality**: Search across all processes by name, description, or process code
- **Process Details**: View complete process information including maps, procedures, and risk registers

#### 2. Document Access
- **Direct Downloads**: Download documents directly from the table view without navigation
- **Secure Downloads**: All document downloads are logged and secured
- **Multiple Document Types**: Access process maps, procedures, and risk registers
- **Version Control**: Documents are versioned to track changes
- **File Type Support**: Supports PDF, Word, Excel, and other common formats
- **Excel-like Interface**: Table view provides familiar spreadsheet-style access

### For Authorized Users (Process Managers, Department Managers, Administrators)

#### 3. Process Management
- **Create Processes**: Add new processes to departments
- **Edit Processes**: Update process information and details
- **Document Upload**: Upload and replace process documents
- **Process Organization**: Assign processes to regions and sections

#### 4. Document Management
- **Upload Documents**: Add new process documents
- **Replace Documents**: Update existing documents with new versions
- **Document Categorization**: Automatic categorization of documents by type

## Getting Started

### Accessing the System

1. Navigate to the main application
2. Click on "Process Management" in the sidebar navigation
3. You'll see the main process list with all departments

### Finding a Process

#### Method 1: Table View (Recommended)
1. From the main process list, ensure "Table View" is selected (default)
2. All processes are displayed in a spreadsheet-like format
3. Use the search box to find processes by name, description, or code
4. Filter by department or region using the dropdown menus
5. Click on process names to view details or download buttons to get documents directly

#### Method 2: Browse by Department
1. Switch to "Departments" view using the toggle
2. Click on any department tile to browse processes in that department
3. Use the region filter to narrow down results
4. Click on any process to view its details

#### Method 3: Search
1. Use the search box at the top of the process list
2. Enter keywords related to the process name, description, or code
3. Results will be filtered in real-time
4. Click on any result to view the process details

### Viewing Process Details

When you click on a process, you'll see:
- **Process Information**: Name, description, department, region, section
- **Process Map**: Visual representation of the process flow
- **Procedure**: Detailed step-by-step instructions
- **Risk Register**: Associated risks and mitigation strategies
- **Download Links**: Direct access to all process documents

### Downloading Documents

#### Method 1: Direct Download from Table View (Fastest)
1. From the main process list in table view
2. Click the download button for the document type you need (Process Map, Procedure, or Risk Register)
3. The document will be downloaded immediately
4. All downloads are logged for audit purposes

#### Method 2: From Process Detail Page
1. Navigate to the process detail page
2. Click on the download link for the document you need
3. The document will be downloaded to your device
4. All downloads are logged for audit purposes

## For Process Managers

### Creating a New Process

1. Navigate to the process management area
2. Click "Create New Process"
3. Fill in the required information:
   - Process name
   - Description
   - Department
   - Region (optional)
   - Section (optional)
4. Save the process
5. Upload associated documents

### Uploading Documents

1. Go to the process detail page
2. Click "Upload Document"
3. Select the document type (Process Map, Procedure, Risk Register)
4. Choose the file to upload
5. Add version information if needed
6. Submit the upload

### Managing Existing Processes

1. Navigate to the process you want to edit
2. Click "Edit Process" (if you have permission)
3. Update the information as needed
4. Save your changes

## Migration from Legacy System

The system includes a migration tool that can import processes from the existing folder-based system:

### Migration Features
- **Automatic Analysis**: Analyzes existing folder structure
- **Department Mapping**: Maps folders to appropriate departments
- **Document Categorization**: Automatically categorizes documents by type
- **Progress Tracking**: Shows migration progress and results
- **Rollback Support**: Can undo migrations if needed

### Running a Migration

**Note**: Only administrators can run migrations.

1. Use the Django management command: `python manage.py migrate_processes`
2. Available options:
   - `--dry-run`: Preview what would be migrated without making changes
   - `--report-only`: Generate analysis report only
   - `--validate-only`: Check if migration is possible
   - `--force`: Override existing data warnings

## Security and Permissions

### Access Levels

1. **All Users**: Can view processes and download documents
2. **Department Managers**: Can create and edit processes in their department
3. **Process Managers**: Can manage processes across departments
4. **Administrators**: Full access to all features including migration

### Audit Logging

All activities are logged including:
- Process views and searches
- Document downloads
- Process creation and editing
- Document uploads and replacements

## Troubleshooting

### Common Issues

#### "Document not found" error
- The document file may have been moved or deleted
- Contact your system administrator

#### "Access denied" error
- You may not have permission for that action
- Contact your supervisor or system administrator

#### Search returns no results
- Try different keywords
- Check spelling
- Use partial words (the search is flexible)

#### Process not showing in department
- The process may be inactive
- Check with your process manager

### Getting Help

For technical issues or questions:
1. Check this user guide first
2. Contact your department's process manager
3. Contact the system administrator
4. Submit a support ticket through the normal IT channels

## Best Practices

### For Process Managers

1. **Consistent Naming**: Use clear, descriptive names for processes
2. **Regular Updates**: Keep process documents current
3. **Version Control**: Always update version numbers when replacing documents
4. **Documentation**: Include clear descriptions for all processes
5. **Organization**: Assign processes to appropriate regions and sections

### For All Users

1. **Search Effectively**: Use specific keywords for better results
2. **Download Responsibly**: Only download documents you need
3. **Report Issues**: Report broken links or missing documents promptly
4. **Stay Updated**: Check for process updates regularly

## System Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- Valid user account with appropriate permissions
- PDF reader for viewing process documents

## Updates and Changes

This system is actively maintained and updated. New features and improvements are added regularly based on user feedback and organizational needs.

For the latest updates and announcements, check the system dashboard or contact your administrator.