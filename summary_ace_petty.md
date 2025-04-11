# ACE and PettyCash Management Systems Summary

## Project Overview

This project consists of two interconnected Django-based web applications designed to manage internal processes within an organization:

1. **ACE (Asset and Capital Expenditure) System** - Manages organizational assets and capital expenditures
2. **PettyCash Management System** - Handles petty cash transactions and approvals

Both systems share common infrastructure including user management, approval workflows, and organizational structure.

## Organizational Structure

The systems operate within a structured organizational hierarchy:
- **Regions** - Geographical divisions of the organization
- **Sections** - Departmental units within regions
- **Users** - Staff members with specific roles and permissions

## PettyCash Management System

### Core Functionality

The PettyCash system manages the complete lifecycle of petty cash transactions:

1. **Request Creation**
   - Users create petty cash requests with detailed expenditure information
   - Supporting documents (quotations) can be attached
   - Each request receives a unique ID (e.g., PC20240501123)

2. **Multi-stage Approval Workflow**
   - Section Head review and approval
   - Finance officer/authorizer approval
   - Disbursement approval by cashier
   - Full audit trail of all approvals

3. **Disbursement Processing**
   - Multiple payment modes supported (cash, mobile payments)
   - Disbursement tracking with payment details
   - Payee information management

4. **Receipt Management**
   - Upload and verification of expenditure receipts
   - Tracking of actual vs. disbursed amounts

5. **Reporting**
   - Date range, section, and region filtering
   - Excel export functionality
   - Financial analysis and reconciliation

### User Roles

- **Creator/Requestor**: Initiates petty cash requests
- **Approver**: Reviews and approves requests (typically section heads)
- **Disburser/Cashier**: Processes approved disbursements
- **Admin**: Full system access and reporting

### Key Features

- **Notification System**: Users are notified of pending actions
- **Dashboard Views**: Role-specific views showing awaiting actions and actioned items
- **Legacy Data Import**: Support for importing historical petty cash records
- **Document Management**: Storage and retrieval of quotes and receipts
- **Currency Support**: Multi-currency transactions

## ACE (Asset and Capital Expenditure) System

### Core Functionality

The ACE system manages organizational assets and capital expenditures:

1. **Asset Management**
   - Registration and tracking of organizational assets
   - Asset categorization and valuation
   - Depreciation calculation

2. **Budget Management**
   - Capital expenditure budgeting
   - Budget allocation and tracking
   - Variance analysis

3. **Procurement Process**
   - Purchase requisitions
   - Approval workflows for capital expenditures
   - Vendor management

4. **Asset Lifecycle**
   - Acquisition tracking
   - Maintenance records
   - Disposal management

### Integration Points

The ACE and PettyCash systems integrate in several ways:

1. **Shared User Management**: Common user profiles and roles across systems
2. **Approval Workflows**: Similar multi-stage approval processes
3. **Organizational Structure**: Common region/section hierarchy
4. **Notification System**: Unified notification framework
5. **Reporting**: Consolidated financial reporting capabilities

## Technical Architecture

- **Backend Framework**: Django (Python)
- **Database**: Relational database (likely PostgreSQL or MySQL)
- **Authentication**: Django authentication with custom role extensions
- **File Storage**: Local file system for document management
- **Export Formats**: Excel and CSV
- **Notification System**: In-app user notifications

## Security Features

- Role-based access control
- Multi-level approval workflows
- Audit trails for all transactions
- Secure document storage
- Authentication required for all operations

This integrated system provides comprehensive financial management tools tailored to the organization's hierarchical structure and approval requirements.