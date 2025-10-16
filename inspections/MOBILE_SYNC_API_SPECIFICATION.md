# Mobile App Sync API Specification

## Overview
This document provides comprehensive API specifications for the BEApp mobile application to synchronize inspection data with the Django backend server. All sync operations use JWT authentication and follow RESTful conventions.

## Base Configuration

### Authentication
- **Type**: JWT (JSON Web Token)
- **Header**: `Authorization: Bearer <token>`
- **Token Endpoint**: `/api/token/` (existing Django REST framework endpoint)

### Base URL
```
https://your-api-domain.com/inspections/sync/
```

### Common Headers
```http
Content-Type: application/json
Authorization: Bearer <your-jwt-token>
X-CSRFToken: <csrf-token> (if using CSRF protection)
```

### Response Format
All responses follow this structure:
```json
{
  "success": true|false,
  "data": { ... },
  "message": "Optional message",
  "errors": ["Array of error messages if success=false"]
}
```

---

## API Endpoints

### 1. Single Inspection Sync

**Endpoint:** `POST /sync-inspection/`

**Description:** Create or update a single inspection record

**Request Body:**
```json
{
  "id": "optional-uuid-if-updating",
  "consumer_name": "John Smith",
  "inspection_date": "2025-01-15",
  "service_no": "SVC-001",
  "reason_for_inspection": "new_installation",
  "property_supplied": "123 Main Street, Test City",
  "property_owner_name": "John Smith",
  "property_owner_address": "123 Main Street, Test City",
  "contractor": "ABC Electrical Ltd",
  "contractor_address": "456 Contractor Ave, Test City",
  "size_of_mains": "16mm",
  "size_of_mains_conduit": "20mm PVC",
  "consumer_main_switch_type": "MCB",
  "consumer_main_switch_capacity": "60A",
  "consumer_main_switch_setting": "60A",
  "neutrals_fused": "pass",
  "neutral_block_fitted": "pass",
  "earth_electrode_installed": "pass",
  "earth_electrode_type": "Copper rod",
  "all_equipment_bonded_earthed": "pass",
  "insulation_resistance_between": "500V > 1MΩ",
  "insulation_resistance_to_earth": "500V > 1MΩ",
  "earth_continuity_resistance": "<0.5Ω",
  "polarity_switches_plugs": "All correct",
  "socket_outlets_earthed": "pass",
  "socket_outlet_type": "13A BS1363",
  "wiring_type": "PVC singles in conduit",
  "circuit_conductors_correct_size": "pass",
  "wiring_condition": "Good condition",
  "flexible_cord_prohibited_positions": "None found",
  "bathroom_switch_accessible": "pass",
  "unearthed_metal_switches": "None found",
  "conduits_bushed": "pass",
  "conduits_bonded_earth": "pass",
  "conduits_correct_size": "pass",
  "conduits_adequately_supported": "pass",
  "conduits_suitable_type": "pass",
  "max_lighting_points_per_circuit": 8,
  "max_plug_points_per_circuit": 4,
  "total_lighting_points": 12,
  "total_plug_points": 6,
  "appliances_wattages": "Lights: 100W each, Sockets: 3000W total",
  "motors_plant_details": "None",
  "overhead_lines_height": "pass",
  "overhead_lines_conductor_size": "pass",
  "overhead_lines_support": "pass",
  "overhead_lines_general": "pass",
  "overhead_earthwires_fitted": "pass",
  "overhead_lines_protected": "pass",
  "outbuildings_protected": "pass",
  "motor_installations_protected": "pass",
  "commission_switch_details": "Commissioned by inspector",
  "supply_connected_disconnected": "Connected",
  "contractor_notified_defects": "pass",
  "other_features_attention": "None",
  "status": "pending",
  "client_application_id": "uuid-of-application"
}
```

**Success Response:**
```json
{
  "success": true,
  "action": "created|updated",
  "inspection_id": "uuid-of-created-inspection",
  "sync_operation": "uuid-of-sync-operation"
}
```

**Error Response:**
```json
{
  "success": false,
  "errors": ["consumer_name is required", "Invalid inspection date format"],
  "message": "Validation failed"
}
```

### 2. Batch Inspection Sync

**Endpoint:** `POST /sync-inspection-batch/`

**Description:** Sync multiple inspection records in a single request (more efficient for bulk operations)

**Request Body:**
```json
{
  "inspections": [
    {
      "consumer_name": "John Smith",
      "inspection_date": "2025-01-15",
      "service_no": "SVC-001",
      "status": "pending",
      "client_application_id": "uuid-of-application",
      "all_equipment_bonded_earthed": "pass",
      "socket_outlets_earthed": "pass",
      "circuit_conductors_correct_size": "pass"
    },
    {
      "id": "existing-inspection-uuid",
      "consumer_name": "Jane Doe",
      "inspection_date": "2025-01-16",
      "service_no": "SVC-002",
      "status": "in_progress",
      "client_application_id": "uuid-of-application"
    }
  ]
}
```

**Success Response:**
```json
{
  "success": true,
  "results": {
    "processed": 2,
    "successful": 2,
    "failed": 0,
    "errors": []
  }
}
```

### 3. Download Inspection Batch

**Endpoint:** `GET /download-inspection-batch/?ids=uuid1,uuid2,uuid3`

**Description:** Download multiple inspection records by their IDs

**Query Parameters:**
- `ids`: Comma-separated list of inspection UUIDs

**Success Response:**
```json
{
  "success": true,
  "inspections": [
    {
      "id": "uuid1",
      "consumer_name": "John Smith",
      "inspection_date": "2025-01-15",
      "service_no": "SVC-001",
      "status": "completed",
      "all_equipment_bonded_earthed": "pass",
      "socket_outlets_earthed": "pass",
      "circuit_conductors_correct_size": "pass",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T14:20:00Z"
    }
  ],
  "count": 1
}
```

### 4. Incremental Sync

**Endpoint:** `POST /incremental-sync/`

**Description:** Sync only data that has changed since the last sync timestamp

**Request Body:**
```json
{
  "since_timestamp": "2025-01-15T10:00:00Z"
}
```

**Success Response:**
```json
{
  "success": true,
  "records_processed": 5,
  "conflicts_resolved": 2,
  "errors": []
}
```

### 5. Get Sync Status Summary

**Endpoint:** `GET /status-summary/`

**Description:** Get a summary of the user's sync status

**Success Response:**
```json
{
  "recent_syncs_count": 12,
  "successful_syncs_count": 10,
  "success_rate": 83.33,
  "pending_uploads": 3,
  "unresolved_conflicts": 1,
  "last_sync": "2025-01-15T14:30:00Z",
  "sync_health": "warning"
}
```

### 6. Get Inspection Conflicts

**Endpoint:** `GET /inspection-conflicts/`

**Description:** Get all unresolved inspection conflicts for the current user

**Success Response:**
```json
{
  "success": true,
  "conflicts": [
    {
      "id": "conflict-uuid",
      "conflict_type": "inspection_data",
      "entity_type": "inspection",
      "entity_id": "inspection-uuid",
      "local_data": {
        "consumer_name": "John Smith",
        "status": "completed"
      },
      "server_data": {
        "consumer_name": "John Smith",
        "status": "in_progress"
      },
      "resolution": "manual",
      "resolved_at": null
    }
  ],
  "count": 1
}
```

### 7. Resolve Conflict

**Endpoint:** `POST /resolve-conflict/<conflict_id>/`

**Description:** Manually resolve a conflict by choosing which data to keep

**Request Body:**
```json
{
  "resolution": "server_wins|local_wins|merged",
  "resolved_data": {
    "consumer_name": "John Smith",
    "status": "completed"
  },
  "notes": "Manual resolution: Used local data for status"
}
```

**Success Response:**
```json
{
  "success": true,
  "conflict": {
    "id": "conflict-uuid",
    "resolution": "local_wins",
    "resolved_data": {
      "consumer_name": "John Smith",
      "status": "completed"
    },
    "resolved_at": "2025-01-15T15:00:00Z",
    "notes": "Manual resolution: Used local data for status"
  }
}
```

### 8. Sync Dashboard Data

**Endpoint:** `GET /dashboard/`

**Description:** Get comprehensive sync dashboard information

**Success Response:**
```json
{
  "recent_syncs": [
    {
      "id": "sync-op-uuid",
      "operation_type": "full",
      "status": "completed",
      "records_affected": 15,
      "started_at": "2025-01-15T10:00:00Z",
      "completed_at": "2025-01-15T10:05:00Z"
    }
  ],
  "pending_uploads": 3,
  "unresolved_conflicts": 1,
  "statistics": {
    "total_syncs": 25,
    "successful_syncs": 22,
    "failed_syncs": 3,
    "success_rate": 88.0
  }
}
```

---

## Error Handling

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (business rule violations)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "errors": [
    "Specific field error 1",
    "Specific field error 2"
  ],
  "code": "ERROR_CODE"
}
```

### Common Error Codes
- `VALIDATION_ERROR` - Request data validation failed
- `PERMISSION_DENIED` - User doesn't have access to resource
- `NOT_FOUND` - Resource doesn't exist
- `CONFLICT_DETECTED` - Data conflict requires resolution
- `SYNC_FAILED` - General sync operation failure

---

## Usage Examples

### JavaScript/TypeScript Example
```typescript
class SyncService {
  private baseUrl = 'https://api.example.com/inspections/sync';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async syncInspection(inspectionData: any) {
    return this.makeRequest('/sync-inspection/', {
      method: 'POST',
      body: JSON.stringify(inspectionData),
    });
  }

  async syncInspectionBatch(inspections: any[]) {
    return this.makeRequest('/sync-inspection-batch/', {
      method: 'POST',
      body: JSON.stringify({ inspections }),
    });
  }

  async downloadInspections(ids: string[]) {
    const params = new URLSearchParams();
    ids.forEach(id => params.append('ids', id));

    return this.makeRequest(`/download-inspection-batch/?${params}`);
  }

  async getSyncStatus() {
    return this.makeRequest('/status-summary/');
  }

  async resolveConflict(conflictId: string, resolution: string, data?: any) {
    return this.makeRequest(`/resolve-conflict/${conflictId}/`, {
      method: 'POST',
      body: JSON.stringify({
        resolution,
        resolved_data: data,
        notes: 'Resolved via mobile app'
      }),
    });
  }
}
```

### Mobile App Integration Pattern
```typescript
// 1. Authenticate and get token
const token = await authenticateUser(username, password);

// 2. Initialize sync service
const syncService = new SyncService(token);

// 3. Perform initial full sync
const fullSyncResult = await syncService.performFullSync();

// 4. Set up periodic incremental sync
setInterval(async () => {
  const lastSyncTime = await getLastSyncTime();
  await syncService.performIncrementalSync(lastSyncTime);
}, 15 * 60 * 1000); // Every 15 minutes

// 5. Handle conflicts
const conflicts = await syncService.getConflicts();
for (const conflict of conflicts) {
  // Show conflict resolution UI to user
  const resolution = await showConflictResolutionUI(conflict);
  await syncService.resolveConflict(conflict.id, resolution);
}
```

---

## Data Types and Validation

### Inspection Status Values
- `pending` - Inspection not yet started
- `in_progress` - Inspection being conducted
- `completed` - Inspection finished, awaiting approval
- `approved` - Inspection passed
- `rejected` - Inspection failed

### Safety Check Values
- `pass` - Requirement satisfied
- `fail` - Requirement not satisfied
- `na` - Not applicable

### Sync Priority Levels
- `low` - Background sync operations
- `normal` - Standard sync operations
- `high` - Urgent sync operations
- `critical` - Emergency sync operations

---

## Best Practices

### 1. Error Handling
```typescript
try {
  const result = await syncService.syncInspection(inspectionData);
  if (result.success) {
    // Handle success
    updateLocalCache(result.inspection_id);
  } else {
    // Handle validation errors
    showValidationErrors(result.errors);
  }
} catch (error) {
  // Handle network/server errors
  queueForRetry(inspectionData);
}
```

### 2. Conflict Resolution Strategy
```typescript
// 1. Try automatic resolution first
if (canAutoResolve(conflict)) {
  await resolveAutomatically(conflict);
} else {
  // 2. Show manual resolution UI
  const userChoice = await showConflictResolutionUI(conflict);
  await resolveManually(conflict, userChoice);
}
```

### 3. Batch vs Single Operations
```typescript
// Use batch for multiple inspections (more efficient)
if (pendingInspections.length > 3) {
  await syncService.syncInspectionBatch(pendingInspections);
} else {
  // Use single sync for few inspections
  for (const inspection of pendingInspections) {
    await syncService.syncInspection(inspection);
  }
}
```

### 4. Offline Queue Management
```typescript
// When offline, queue operations
if (!navigator.onLine) {
  queueOperation('sync_inspection', inspectionData);
} else {
  // When online, process queue
  const queue = getOfflineQueue();
  for (const operation of queue) {
    await processQueuedOperation(operation);
  }
}
```

---

## Testing the API

### Using curl
```bash
# Sync single inspection
curl -X POST https://api.example.com/inspections/sync/sync-inspection/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "consumer_name": "Test User",
    "inspection_date": "2025-01-15",
    "service_no": "TEST-001",
    "status": "pending"
  }'

# Get sync status
curl -X GET https://api.example.com/inspections/sync/status-summary/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Download inspections
curl -X GET "https://api.example.com/inspections/sync/download-inspection-batch/?ids=uuid1,uuid2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Postman Collection
A Postman collection with all endpoints and example requests is available in the project repository at `docs/postman/inspection-sync-api.json`.

---

## Support and Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check JWT token validity
   - Ensure token is included in Authorization header

2. **403 Forbidden**
   - User doesn't have permission to access the inspection
   - Check if inspection is assigned to the user

3. **422 Unprocessable Entity**
   - Business rule violation (e.g., invalid status transition)
   - Check validation rules for the specific operation

4. **Conflict Detection**
   - Data conflicts are normal and expected
   - Use the conflict resolution endpoints to handle them

### Getting Help
- Check the API logs in the Django admin
- Review the sync operation history
- Contact the backend development team for API issues

---

*This specification will be updated as new features are added to the sync system.*
