# BEApp Django Server API Documentation
## Mobile App Integration Requirements

**Version:** 1.0  
**Date:** September 19, 2025  
**Base URL:** `https://api.beapp.zw/api/v1`  
**Environment:** Production | Staging | Development

## Table of Contents
1. [Authentication](#authentication)
2. [Application Management](#application-management)
3. [Customer Management](#customer-management)
4. [Contractor Management](#contractor-management)
5. [Inspection Management](#inspection-management)
6. [File Management](#file-management)
7. [Sync Management](#sync-management)
8. [Data Models](#data-models)
9. [Error Handling](#error-handling)

---

## Authentication

### Base URL Structure
```
Development: http://localhost:8000/api/v1
Staging: https://api-staging.beapp.zw/api/v1
Production: https://api.beapp.zw/api/v1
```

### Authentication Endpoints

#### POST `/auth/login`
**Description:** Field officer login with JWT token generation
**Method:** POST
**Content-Type:** application/json

**Request Body:**
```json
{
  "username": "field_officer_001",
  "password": "securePassword123",
  "deviceId": "device_1726749123_abc123xyz"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 3600,
  "user": {
    "id": "user123",
    "username": "field_officer_001",
    "fullName": "John Doe",
    "email": "john.doe@beapp.zw",
    "phone": "+263771234567",
    "role": "field_officer",
    "employeeId": "EMP001",
    "district": "Harare",
    "region": "Northern",
    "isActive": true,
    "lastLogin": "2025-09-19T10:00:00Z"
  }
}
```

#### POST `/auth/refresh`
**Description:** Refresh expired JWT token
**Method:** POST
**Headers:** Authorization: Bearer {refresh_token}

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 3600
}
```

#### POST `/auth/logout`
**Description:** Logout and invalidate tokens
**Method:** POST
**Headers:** Authorization: Bearer {access_token}

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

#### GET `/auth/profile`
**Description:** Get current user profile
**Method:** GET
**Headers:** Authorization: Bearer {access_token}

**Response (200 OK):**
```json
{
  "id": "user123",
  "username": "field_officer_001",
  "fullName": "John Doe",
  "email": "john.doe@beapp.zw",
  "role": "field_officer",
  "permissions": {
    "canViewAssignments": true,
    "canAcceptAssignments": true,
    "canCreateInspections": true,
    "canCompleteInspections": true,
    "canViewAllInspections": false,
    "canApproveInspections": false
  }
}
```

---

## Application Management

### GET `/applications/assigned`
**Description:** Get applications assigned to current field officer
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**Query Parameters:**
- `officer_id`: string (optional, defaults to current user)
- `include_details`: boolean (default: true)
- `since`: ISO date string (for incremental sync)

**Response (200 OK):**
```json
{
  "applications": [
    {
      "id": "app_12345",
      "application_number": "APP-20250919-001",
      "application_type": "new_installation",
      "priority": "high",
      "customer": {
        "serverId": "cust_123",
        "customerId": "CUST-20250915-001",
        "fullName": "Jane Smith",
        "phone": "+263771234567",
        "email": "jane.smith@email.com",
        "standPlotNumber": "123",
        "farmStreetName": "Main Street",
        "suburbTownship": "Avondale",
        "district": "Harare",
        "isActive": true
      },
      "contractor": {
        "serverId": "cont_456",
        "contractorId": "CONT-20250915-001",
        "businessName": "Elite Electrical Services",
        "contactPerson": "Mike Johnson",
        "phone": "+263772345678",
        "email": "mike@eliteelectrical.zw",
        "licenseNumber": "ELC001",
        "isActive": true
      },
      "attachments": [
        {
          "serverId": "att_789",
          "applicationServerId": "app_12345",
          "fileUrl": "https://api.beapp.zw/files/att_789/download",
          "fileType": "E21",
          "description": "Electrical Installation Certificate",
          "fileSize": 2048576,
          "uploadedAt": "2025-09-19T08:00:00Z",
          "isCached": false
        }
      ],
      "purpose": "domestic",
      "supply_type": "permanent",
      "status": "assigned",
      "assignment_status": "assigned",
      "assigned_to": "user123",
      "due_date": "2025-09-25T17:00:00Z",
      "created_at": "2025-09-19T08:00:00Z",
      "updated_at": "2025-09-19T09:00:00Z"
    }
  ],
  "total_count": 1,
  "pending_count": 1,
  "overdue_count": 0,
  "accepted_count": 0
}
```

### GET `/applications/:id`
**Description:** Get detailed application information
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**URL Parameters:** `id` - Application ID

**Response (200 OK):** Same as single application object above

### PATCH `/applications/:id/status`
**Description:** Update application status
**Method:** PATCH
**Headers:** Authorization: Bearer {access_token}
**URL Parameters:** `id` - Application ID

**Request Body:**
```json
{
  "status": "in_progress",
  "assignment_status": "in_progress",
  "notes": "Started inspection process"
}
```

**Response (200 OK):**
```json
{
  "message": "Application status updated successfully",
  "application": {
    "id": "app_12345",
    "status": "in_progress",
    "assignment_status": "in_progress",
    "updated_at": "2025-09-19T11:00:00Z"
  }
}
```

### GET `/applications/:id/attachments`
**Description:** Get application attachments
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**URL Parameters:** `id` - Application ID

**Response (200 OK):**
```json
{
  "attachments": [
    {
      "serverId": "att_789",
      "fileUrl": "https://api.beapp.zw/files/att_789/download",
      "fileType": "E21",
      "description": "Electrical Installation Certificate",
      "fileSize": 2048576,
      "uploadedAt": "2025-09-19T08:00:00Z"
    }
  ]
}
```

### POST `/applications/:id/accept`
**Description:** Accept an assigned application
**Method:** POST
**Headers:** Authorization: Bearer {access_token}
**URL Parameters:** `id` - Application ID

**Request Body:**
```json
{
  "acceptance_notes": "Assignment accepted, will begin inspection tomorrow"
}
```

**Response (200 OK):**
```json
{
  "message": "Assignment accepted successfully",
  "assignment_status": "accepted",
  "accepted_at": "2025-09-19T11:00:00Z"
}
```

### POST `/applications/:id/complete`
**Description:** Complete an assignment with inspection results
**Method:** POST
**Headers:** Authorization: Bearer {access_token}
**URL Parameters:** `id` - Application ID

**Request Body:**
```json
{
  "inspection_id": "insp_12345",
  "completion_notes": "Inspection completed successfully, all points passed",
  "inspection_result": "passed",
  "defects_count": 0
}
```

**Response (200 OK):**
```json
{
  "message": "Assignment completed successfully",
  "status": "completed",
  "assignment_status": "completed",
  "completed_at": "2025-09-19T15:00:00Z"
}
```

---

## Customer Management

### GET `/customers`
**Description:** Get customers list with pagination
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**Query Parameters:**
- `page`: number (default: 1)
- `limit`: number (default: 50, max: 100)
- `since`: ISO date string (for incremental sync)

**Response (200 OK):**
```json
{
  "data": [
    {
      "serverId": "cust_123",
      "customerId": "CUST-20250915-001",
      "fullName": "Jane Smith",
      "phone": "+263771234567",
      "email": "jane.smith@email.com",
      "standPlotNumber": "123",
      "farmStreetName": "Main Street",
      "suburbTownship": "Avondale",
      "district": "Harare",
      "isActive": true,
      "created_at": "2025-09-15T10:00:00Z",
      "updated_at": "2025-09-15T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 150
  }
}
```

### GET `/customers/:id`
**Description:** Get customer details by ID
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**URL Parameters:** `id` - Customer ID

**Response (200 OK):** Single customer object as above

### GET `/customers/search`
**Description:** Search customers by name, ID, or phone
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**Query Parameters:**
- `q`: string (search term)
- `limit`: number (default: 20)

**Response (200 OK):**
```json
{
  "results": [
    {
      "serverId": "cust_123",
      "customerId": "CUST-20250915-001",
      "fullName": "Jane Smith",
      "phone": "+263771234567",
      "district": "Harare"
    }
  ],
  "count": 1
}
```

---

## Contractor Management

### GET `/contractors`
**Description:** Get contractors list with pagination
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**Query Parameters:**
- `page`: number (default: 1)
- `limit`: number (default: 50)
- `since`: ISO date string (for incremental sync)

**Response (200 OK):**
```json
{
  "data": [
    {
      "serverId": "cont_456",
      "contractorId": "CONT-20250915-001",
      "businessName": "Elite Electrical Services",
      "contactPerson": "Mike Johnson",
      "phone": "+263772345678",
      "email": "mike@eliteelectrical.zw",
      "address": "15 Industrial Road, Msasa, Harare",
      "licenseNumber": "ELC001",
      "businessRegistration": "BR12345",
      "isActive": true,
      "created_at": "2025-09-15T10:00:00Z",
      "updated_at": "2025-09-15T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 75
  }
}
```

### GET `/contractors/:id`
**Description:** Get contractor details by ID
**Method:** GET
**Headers:** Authorization: Bearer {access_token}

### GET `/contractors/search`
**Description:** Search contractors by name, license, or registration
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**Query Parameters:**
- `q`: string (search term)
- `limit`: number (default: 20)

---

## Inspection Management

### POST `/inspections`
**Description:** Create or upload inspection data
**Method:** POST
**Headers:** Authorization: Bearer {access_token}
**Content-Type:** application/json

**Request Body:**
```json
{
  "id": "insp_12345",
  "serviceNumber": "12345678",
  "applicationType": "new_installation",
  "consumerDetails": {
    "fullName": "Jane Smith",
    "phoneNumber": "+263771234567",
    "standNumber": "123",
    "streetName": "Main Street"
  },
  "propertyDetails": {
    "suburbTownship": "Avondale",
    "district": "Harare"
  },
  "contractorDetails": {
    "businessName": "Elite Electrical Services",
    "contactPerson": "Mike Johnson"
  },
  "inspectionPoints": {
    "point1": { "status": "compliant", "notes": "Earthing system properly installed" },
    "point2": { "status": "compliant", "notes": "Main switch accessible" }
  },
  "overallResult": "passed",
  "defectsCount": 0,
  "inspectorSignature": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "gpsCoordinates": {
    "latitude": -17.8216,
    "longitude": 31.0492,
    "accuracy": 5.2
  },
  "status": "completed",
  "createdAt": "2025-09-19T10:00:00Z",
  "completedAt": "2025-09-19T14:00:00Z",
  "applicationId": "app_12345"
}
```

**Response (201 Created):**
```json
{
  "id": "insp_12345",
  "server_id": "srv_insp_456",
  "message": "Inspection created successfully",
  "created_at": "2025-09-19T14:30:00Z"
}
```

### POST `/inspections/:id/upload`
**Description:** Upload complete inspection data (alternative to POST /inspections)
**Method:** POST
**Headers:** Authorization: Bearer {access_token}

### POST `/inspections/:id/photos`
**Description:** Upload inspection photos
**Method:** POST
**Headers:** Authorization: Bearer {access_token}
**Content-Type:** multipart/form-data

**Request Body (FormData):**
```
files[]: File (multiple photo files)
inspection_id: string
metadata: JSON string with photo details
```

**Response (200 OK):**
```json
{
  "uploaded_photos": [
    {
      "id": "photo_123",
      "filename": "point_1_earthing.jpg",
      "url": "https://api.beapp.zw/files/photo_123/download",
      "inspection_point": "1",
      "uploaded_at": "2025-09-19T14:35:00Z"
    }
  ]
}
```

### POST `/inspections/:id/signatures`
**Description:** Upload digital signatures
**Method:** POST
**Headers:** Authorization: Bearer {access_token}
**Content-Type:** application/json

**Request Body:**
```json
{
  "inspector_signature": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "customer_signature": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "signature_timestamp": "2025-09-19T14:00:00Z"
}
```

### PATCH `/inspections/:id/status`
**Description:** Update inspection status
**Method:** PATCH
**Headers:** Authorization: Bearer {access_token}

**Request Body:**
```json
{
  "status": "completed",
  "notes": "All inspection points verified"
}
```

---

## File Management

### GET `/files/:id/download`
**Description:** Download file by ID
**Method:** GET
**Headers:** Authorization: Bearer {access_token}
**URL Parameters:** `id` - File ID

**Response (200 OK):**
- Content-Type: application/octet-stream (or appropriate MIME type)
- Content-Disposition: attachment; filename="document.pdf"
- File binary data

### POST `/files/upload`
**Description:** Upload files
**Method:** POST
**Headers:** Authorization: Bearer {access_token}
**Content-Type:** multipart/form-data

**Request Body (FormData):**
```
file: File
category: string (e.g., "inspection_photo", "signature", "attachment")
description: string (optional)
metadata: JSON string (optional)
```

**Response (201 Created):**
```json
{
  "id": "file_123",
  "filename": "inspection_photo.jpg",
  "url": "https://api.beapp.zw/files/file_123/download",
  "size": 1024567,
  "mime_type": "image/jpeg",
  "uploaded_at": "2025-09-19T14:40:00Z"
}
```

---

## Sync Management

### GET `/sync/status`
**Description:** Get synchronization status
**Method:** GET
**Headers:** Authorization: Bearer {access_token}

**Response (200 OK):**
```json
{
  "last_full_sync": "2025-09-19T08:00:00Z",
  "last_incremental_sync": "2025-09-19T14:00:00Z",
  "pending_uploads": 0,
  "failed_operations": 0,
  "sync_available": true,
  "server_time": "2025-09-19T14:45:00Z"
}
```

### POST `/sync/incremental`
**Description:** Perform incremental synchronization
**Method:** POST
**Headers:** Authorization: Bearer {access_token}

**Request Body:**
```json
{
  "last_sync_time": "2025-09-19T08:00:00Z",
  "data_types": ["applications", "customers", "contractors", "attachments"]
}
```

**Response (200 OK):**
```json
{
  "sync_completed": true,
  "updated_records": {
    "applications": 5,
    "customers": 2,
    "contractors": 1,
    "attachments": 3
  },
  "sync_time": "2025-09-19T14:45:00Z"
}
```

### POST `/sync/full`
**Description:** Perform full synchronization
**Method:** POST
**Headers:** Authorization: Bearer {access_token}

### POST `/sync/upload`
**Description:** Upload queued changes from mobile app
**Method:** POST
**Headers:** Authorization: Bearer {access_token}

**Request Body:**
```json
{
  "operations": [
    {
      "id": "upload_123",
      "table_name": "inspections",
      "record_id": "insp_12345",
      "operation": "create",
      "data": { /* inspection data */ },
      "priority": 1,
      "created_at": "2025-09-19T14:00:00Z"
    }
  ]
}
```

---

## Data Models

### User Roles and Permissions
```python
# Django models.py example
class UserRole(models.TextChoices):
    FIELD_OFFICER = 'field_officer', 'Field Officer'
    SUPERVISOR = 'supervisor', 'Supervisor'
    ADMIN = 'admin', 'Admin'

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    employee_id = models.CharField(max_length=20, unique=True)
    district = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
```

### Application States
```python
class ApplicationStatus(models.TextChoices):
    SUBMITTED = 'submitted', 'Submitted'
    ASSIGNED = 'assigned', 'Assigned'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    REJECTED = 'rejected', 'Rejected'

class AssignmentStatus(models.TextChoices):
    ASSIGNED = 'assigned', 'Assigned'
    ACCEPTED = 'accepted', 'Accepted'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "message": "Human readable error message",
    "code": "ERROR_CODE",
    "details": {
      "field": "validation error details"
    }
  },
  "status": 400
}
```

### HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server error

### Common Error Codes
- `AUTHENTICATION_REQUIRED` - Token missing or invalid
- `INVALID_TOKEN` - JWT token expired or malformed
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `VALIDATION_ERROR` - Request data validation failed
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `ASSIGNMENT_CONFLICT` - Assignment already accepted/completed

---

## Rate Limiting
- Authentication endpoints: 5 requests per minute per IP
- General API endpoints: 100 requests per minute per user
- File upload endpoints: 20 requests per minute per user

## Security Headers Required
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## CORS Configuration
- Allow origins: Mobile app domains
- Allow methods: GET, POST, PATCH, DELETE, OPTIONS
- Allow headers: Authorization, Content-Type, X-Requested-With

---

**Last Updated:** September 19, 2025  
**Contact:** BEApp Development Team  
**Support:** technical-support@beapp.zw