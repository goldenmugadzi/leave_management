# Assignment Management API Specification

## Overview

This document specifies the API requirements for the Assignment Management system in BEApp. The mobile application needs to fetch, display, and manage electrical inspection assignments assigned to field officers.

## Base Configuration

### Environment URLs
- **Development**: `http://localhost:8000/api/v1`
- **Staging**: `https://api-staging.beapp.zw/api/v1`
- **Production**: `https://api.beapp.zw/api/v1`

### Timeout Configuration
- **Default requests**: 10-20 seconds
- **File downloads**: 30 seconds
- **Sync operations**: 2 minutes

## Authentication

All assignment endpoints require authentication via JWT token in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

The token should contain the field officer's user ID and role information.

## Core Data Structures

### Application Assignment Response

```typescript
interface AssignmentResponse {
  applications: ServerApplicationResponse[];
  total_count: number;
  pending_count: number;
  overdue_count: number;
  accepted_count: number;
}
```

### Server Application Response

```typescript
interface ServerApplicationResponse {
  id: string;                    // Unique server ID
  application_number: string;    // Format: APP-YYYYMMDD-XXXXXXXX
  application_type: 'new_installation' | 'statutory_inspection' | 'change_of_tenancy' | 'reconnection';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  customer: CustomerCache;
  contractor: ContractorCache;
  attachments: ApplicationAttachmentCache[];
  purpose: 'domestic' | 'commercial' | 'agricultural' | 'public_lighting' | 'industrial';
  supply_type: 'permanent' | 'temporary';
  status: 'submitted' | 'assigned' | 'in_progress' | 'completed' | 'rejected';
  assignment_status: 'assigned' | 'accepted' | 'in_progress' | 'completed';
  assigned_to?: string;          // Field officer user ID
  due_date?: string;            // ISO 8601 format
  created_at: string;           // ISO 8601 format
  updated_at: string;           // ISO 8601 format
}
```

### Customer Data Structure

```typescript
interface CustomerCache {
  serverId: string;             // Unique server ID
  customerId: string;           // Format: CUST-YYYYMMDD-XXXXXXXX
  fullName: string;
  phone?: string;
  email?: string;
  standPlotNumber?: string;
  farmStreetName?: string;
  suburbTownship?: string;
  district?: string;
  lastSynced: string;           // ISO 8601 format
  cacheExpires: string;         // ISO 8601 format
  isActive: boolean;
}
```

### Contractor Data Structure

```typescript
interface ContractorCache {
  serverId: string;             // Unique server ID
  contractorId: string;         // Format: CONT-YYYYMMDD-XXXXXXXX
  businessName: string;
  contactPerson?: string;
  phone?: string;
  email?: string;
  address?: string;
  licenseNumber?: string;
  businessRegistration?: string;
  lastSynced: string;           // ISO 8601 format
  cacheExpires: string;         // ISO 8601 format
  isActive: boolean;
}
```

### Application Attachment Structure

```typescript
interface ApplicationAttachmentCache {
  serverId: string;
  applicationServerId: string;
  fileUrl: string;              // Server URL for download
  localFilePath?: string;       // Local cached file path (mobile only)
  fileType: 'E21' | 'E22' | 'E25' | 'other';
  description?: string;
  fileSize?: number;            // Size in bytes
  uploadedAt: string;           // ISO 8601 format
  downloadedAt?: string;        // ISO 8601 format (mobile only)
  isCached: boolean;            // Mobile only flag
}
```

## API Endpoints

### 1. Get Assigned Applications

**Endpoint**: `GET /applications/assigned`

**Description**: Retrieves all applications assigned to the authenticated field officer.

**Query Parameters**:
- `officer_id` (string, required): Field officer's user ID
- `include_details` (boolean, optional): Include full customer/contractor details (default: true)
- `status` (string, optional): Filter by assignment status ('assigned', 'accepted', 'in_progress', 'completed')
- `priority` (string, optional): Filter by priority ('low', 'normal', 'high', 'urgent')
- `due_date_from` (string, optional): Filter applications due after this date (ISO 8601)
- `due_date_to` (string, optional): Filter applications due before this date (ISO 8601)
- `page` (number, optional): Page number for pagination (default: 1)
- `limit` (number, optional): Number of records per page (default: 50, max: 100)

**Request Example**:
```http
GET /api/v1/applications/assigned?officer_id=user123&include_details=true&status=assigned
Authorization: Bearer <jwt_token>
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "applications": [
      {
        "id": "app_001",
        "application_number": "APP-20250920-001234",
        "application_type": "new_installation",
        "priority": "high",
        "customer": {
          "serverId": "cust_001",
          "customerId": "CUST-20250920-001234",
          "fullName": "John Mukasa",
          "phone": "+263771234567",
          "email": "john.mukasa@email.com",
          "standPlotNumber": "123",
          "farmStreetName": "Main Street",
          "suburbTownship": "Harare",
          "district": "Harare",
          "lastSynced": "2025-09-20T10:00:00Z",
          "cacheExpires": "2025-09-21T10:00:00Z",
          "isActive": true
        },
        "contractor": {
          "serverId": "cont_001",
          "contractorId": "CONT-20250920-001234",
          "businessName": "ABC Electrical Services",
          "contactPerson": "Peter Smith",
          "phone": "+263771234568",
          "email": "peter@abcelectrical.com",
          "address": "456 Industrial Road, Harare",
          "licenseNumber": "ELC-2025-001",
          "businessRegistration": "BR-2025-001",
          "lastSynced": "2025-09-20T10:00:00Z",
          "cacheExpires": "2025-09-21T10:00:00Z",
          "isActive": true
        },
        "attachments": [
          {
            "serverId": "att_001",
            "applicationServerId": "app_001",
            "fileUrl": "https://api.beapp.zw/files/att_001/download",
            "fileType": "E21",
            "description": "Application Form E21",
            "fileSize": 2048576,
            "uploadedAt": "2025-09-20T09:00:00Z",
            "isCached": false
          }
        ],
        "purpose": "domestic",
        "supply_type": "permanent",
        "status": "assigned",
        "assignment_status": "assigned",
        "assigned_to": "user123",
        "due_date": "2025-09-25T17:00:00Z",
        "created_at": "2025-09-20T08:00:00Z",
        "updated_at": "2025-09-20T10:00:00Z"
      }
    ],
    "total_count": 15,
    "pending_count": 8,
    "overdue_count": 2,
    "accepted_count": 5
  },
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 15
  }
}
```

### 2. Get Application Details

**Endpoint**: `GET /applications/{id}`

**Description**: Retrieves detailed information for a specific application.

**Path Parameters**:
- `id` (string, required): Application server ID

**Request Example**:
```http
GET /api/v1/applications/app_001
Authorization: Bearer <jwt_token>
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "app_001",
    "application_number": "APP-20250920-001234",
    "application_type": "new_installation",
    "priority": "high",
    "customer": { /* Customer object as above */ },
    "contractor": { /* Contractor object as above */ },
    "attachments": [ /* Attachment objects as above */ ],
    "purpose": "domestic",
    "supply_type": "permanent",
    "status": "assigned",
    "assignment_status": "assigned",
    "assigned_to": "user123",
    "due_date": "2025-09-25T17:00:00Z",
    "created_at": "2025-09-20T08:00:00Z",
    "updated_at": "2025-09-20T10:00:00Z",
    "additional_details": {
      "installation_address": "123 Main Street, Harare",
      "meter_type": "Single Phase",
      "load_requirement": "5kW",
      "special_instructions": "Access through back gate"
    }
  }
}
```

### 3. Accept Assignment

**Endpoint**: `POST /applications/{id}/accept`

**Description**: Allows a field officer to accept an assigned application.

**Path Parameters**:
- `id` (string, required): Application server ID

**Request Body**:
```json
{
  "officer_id": "user123",
  "accepted_at": "2025-09-20T11:00:00Z",
  "estimated_completion": "2025-09-22T16:00:00Z",
  "notes": "Will inspect on Monday morning"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "app_001",
    "assignment_status": "accepted",
    "accepted_at": "2025-09-20T11:00:00Z",
    "updated_at": "2025-09-20T11:00:00Z"
  },
  "message": "Assignment accepted successfully"
}
```

### 4. Update Assignment Status

**Endpoint**: `PATCH /applications/{id}/status`

**Description**: Updates the status of an application assignment.

**Path Parameters**:
- `id` (string, required): Application server ID

**Request Body**:
```json
{
  "assignment_status": "in_progress",
  "status": "in_progress",
  "officer_id": "user123",
  "updated_at": "2025-09-20T12:00:00Z",
  "notes": "Started inspection process",
  "location": {
    "latitude": -17.8252,
    "longitude": 31.0335
  }
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "app_001",
    "assignment_status": "in_progress",
    "status": "in_progress",
    "updated_at": "2025-09-20T12:00:00Z"
  },
  "message": "Status updated successfully"
}
```

### 5. Complete Assignment

**Endpoint**: `POST /applications/{id}/complete`

**Description**: Marks an application assignment as completed.

**Path Parameters**:
- `id` (string, required): Application server ID

**Request Body**:
```json
{
  "officer_id": "user123",
  "completed_at": "2025-09-22T15:30:00Z",
  "inspection_result": "passed",
  "inspection_id": "insp_001",
  "completion_notes": "Installation meets all safety requirements",
  "photos_uploaded": true,
  "documents_uploaded": true
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "app_001",
    "assignment_status": "completed",
    "status": "completed",
    "completed_at": "2025-09-22T15:30:00Z",
    "inspection_id": "insp_001",
    "updated_at": "2025-09-22T15:30:00Z"
  },
  "message": "Assignment completed successfully"
}
```

### 6. Get Application Attachments

**Endpoint**: `GET /applications/{id}/attachments`

**Description**: Retrieves all attachments for a specific application.

**Path Parameters**:
- `id` (string, required): Application server ID

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "attachments": [
      {
        "serverId": "att_001",
        "applicationServerId": "app_001",
        "fileUrl": "https://api.beapp.zw/files/att_001/download",
        "fileType": "E21",
        "description": "Application Form E21",
        "fileSize": 2048576,
        "uploadedAt": "2025-09-20T09:00:00Z",
        "isCached": false
      },
      {
        "serverId": "att_002",
        "applicationServerId": "app_001",
        "fileUrl": "https://api.beapp.zw/files/att_002/download",
        "fileType": "E22",
        "description": "Site Plan",
        "fileSize": 1024768,
        "uploadedAt": "2025-09-20T09:15:00Z",
        "isCached": false
      }
    ]
  }
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "error": {
    "message": "Human-readable error message",
    "status": 400,
    "code": "ERROR_CODE",
    "details": {
      "field": "Specific field error details"
    }
  }
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Invalid request parameters or body |
| 401 | `UNAUTHENTICATED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | User doesn't have permission for this resource |
| 404 | `NOT_FOUND` | Application or resource not found |
| 409 | `CONFLICT` | Assignment already accepted by another officer |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server internal error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### Error Examples

**Authentication Error** (401):
```json
{
  "success": false,
  "error": {
    "message": "Authentication token is missing or invalid",
    "status": 401,
    "code": "UNAUTHENTICATED"
  }
}
```

**Validation Error** (422):
```json
{
  "success": false,
  "error": {
    "message": "Validation failed",
    "status": 422,
    "code": "VALIDATION_ERROR",
    "details": {
      "officer_id": "Officer ID is required",
      "assignment_status": "Invalid status value"
    }
  }
}
```

**Assignment Conflict** (409):
```json
{
  "success": false,
  "error": {
    "message": "Assignment has already been accepted by another officer",
    "status": 409,
    "code": "ASSIGNMENT_CONFLICT",
    "details": {
      "current_assignee": "user456",
      "accepted_at": "2025-09-20T10:30:00Z"
    }
  }
}
```

## Caching and Offline Support

### Cache Headers

The API should include appropriate cache headers for offline support:

```http
Cache-Control: max-age=3600, must-revalidate
ETag: "abc123def456"
Last-Modified: Wed, 20 Sep 2025 10:00:00 GMT
```

### Offline Behavior

1. **Cache Duration**: Application data should be cached for 24 hours
2. **Stale Data**: Mobile app can use stale data up to 7 days when offline
3. **Sync Priority**: Assignment status changes have high priority for sync
4. **Conflict Resolution**: Server timestamp wins in case of conflicts

## Rate Limiting

- **Standard endpoints**: 100 requests per minute per user
- **File downloads**: 20 requests per minute per user
- **Status updates**: 50 requests per minute per user

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1695211200
```

## Security Considerations

1. **Authentication**: All endpoints require valid JWT token
2. **Authorization**: Officers can only access their assigned applications
3. **Data Validation**: All input data must be validated and sanitized
4. **File Access**: Attachment URLs should be signed and time-limited
5. **Audit Logging**: All assignment status changes should be logged

## Performance Requirements

1. **Response Time**: 
   - List endpoints: < 2 seconds
   - Detail endpoints: < 1 second
   - Status updates: < 500ms

2. **Throughput**:
   - Support 100 concurrent field officers
   - Handle 1000 requests per minute during peak hours

3. **Availability**: 99.9% uptime during business hours

## Testing Requirements

### Test Data Requirements

1. **Sample Applications**: Provide at least 20 test applications with various:
   - Application types (new_installation, statutory_inspection, etc.)
   - Priorities (low, normal, high, urgent)
   - Assignment statuses (assigned, accepted, in_progress, completed)
   - Due dates (past, present, future)

2. **Test Users**: Provide test field officer accounts with different assignment loads

3. **File Attachments**: Include sample E21, E22, E25 forms and other document types

### API Testing Checklist

- [ ] Authentication with valid/invalid tokens
- [ ] Authorization for different user roles
- [ ] Pagination with various page sizes
- [ ] Filtering by all supported parameters
- [ ] Assignment acceptance/rejection flows
- [ ] Status update workflows
- [ ] Error handling for all error codes
- [ ] Rate limiting behavior
- [ ] File download functionality
- [ ] Offline/online sync scenarios

## Implementation Priority

### Phase 1 (Critical)
1. GET `/applications/assigned` - Core assignment listing
2. POST `/applications/{id}/accept` - Assignment acceptance
3. PATCH `/applications/{id}/status` - Status updates
4. Basic error handling and authentication

### Phase 2 (Important)
1. GET `/applications/{id}` - Detailed application view
2. GET `/applications/{id}/attachments` - File attachments
3. POST `/applications/{id}/complete` - Assignment completion
4. Enhanced filtering and pagination

### Phase 3 (Nice to Have)
1. Advanced search capabilities
2. Bulk operations
3. Real-time notifications
4. Advanced analytics endpoints

## Support and Maintenance

- **API Documentation**: Keep this document updated with any changes
- **Versioning**: Use semantic versioning for API changes
- **Deprecation**: Provide 3-month notice for breaking changes
- **Monitoring**: Implement comprehensive API monitoring and alerting
- **Backup**: Ensure all assignment data is backed up regularly
