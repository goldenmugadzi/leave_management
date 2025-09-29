# Inspection Assignment Sync Backend Contracts

## Motivation and Current Gaps

Mobile assignment synchronization currently blocks on the lack of concrete backend contracts. The existing `inspectionSyncService` stubs, Postman collection items (e.g. `/assignments/sync/`, `/approvals/sync/`), and mobile spec make assumptions about request payloads, response envelopes, and local storage that do not exist. This document defines the contracts required to unblock:

- Local persistence for assignments and approvals (to be added to `schema.ts` and SQLite migrations)
- Mapper helpers that translate between server payloads and local models
- Incremental download logic and sync timestamps
- Upload/approval/merge hooks (workflow transitions, conflict detection, resolution)
- Postman collection updates with real payload examples

All endpoints share the base path `https://your-api-domain.com/inspections/sync/` and must be exposed under DRF viewsets that respect JWT auth headers already defined in the mobile spec. API path constants should be registered in `apiEndpoints.ts` rather than hardcoded elsewhere.

## Domain Entities and Storage Contracts

### Server-side Models

| Entity | Purpose | Key Fields |
| --- | --- | --- |
| `InspectionAssignment` | Tracks who must action an inspection and the mobile delivery lifecycle | `id` (UUID), `inspection_id`, `assigned_to` (user UUID), `assigned_team` (optional), `status`, `priority`, `due_at`, `server_updated_at`, `last_transition_id` |
| `AssignmentApproval` | Represents workflow approvals attached to an assignment (team lead sign-off, QA, etc.) | `id` (UUID), `assignment_id`, `step_code`, `actor_id`, `decision` (enum), `comment`, `decided_at`, `requires_merge`, `server_updated_at` |
| `AssignmentSyncAudit` | Records sync handshake state per device | `id` (UUID), `assignment_id`, `device_id`, `last_downloaded_at`, `last_uploaded_at`, `conflict_state` |

### Mobile Persistence (New SQLite Tables)

Add the following definitions to `schema.ts` in the mobile client and generate migrations accordingly:

| Table | Fields | Notes |
| --- | --- | --- |
| `inspectionAssignments` | `id`, `inspectionId`, `assignedTo`, `assignedTeam`, `status`, `priority`, `dueAt`, `acknowledgedAt`, `completedAt`, `serverUpdatedAt`, `localUpdatedAt`, `dirty`, `lastSyncAction`, `conflictState`, `payloadHash` | `localUpdatedAt` drives incremental uploads; `dirty` flags unsynced local edits; `payloadHash` helps detect stale payload mismatches |
| `inspectionAssignmentApprovals` | `id`, `assignmentId`, `stepCode`, `actorId`, `decision`, `comment`, `decidedAt`, `requiresMerge`, `serverUpdatedAt`, `localUpdatedAt`, `dirty` | Mirror server approvals and support offline editing |
| `inspectionAssignmentSyncLog` | `id`, `assignmentId`, `deviceId`, `direction`, `status`, `operation`, `httpCode`, `createdAt` | Optional table for debugging sync attempts |

## Status Machines

### Assignment Status Enum

`assigned` → `acknowledged` → `in_progress` → `completed`

Additional transitions: `assigned` → `rejected`, `in_progress` → `blocked`, `blocked` → `in_progress`, `any` → `cancelled` (admin only).

Constraints:

- Only the assignee (or delegate) can move to `acknowledged`/`in_progress`/`completed`.
- `rejected` requires a `rejectionReason` payload and resets `priority`/`due_at` on reassignment.
- `blocked` must include `blockerCategory` and `notes`.

### Approval Decision Enum

`pending`, `approved`, `rejected`, `needs_changes`, `auto_approved`.

Approval transitions require `step_code` (e.g. `team_lead`, `qa`, `regional_manager`) and optional merge metadata.

## API Surface

All responses follow the standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "message": "",
  "errors": []
}
```

### 1. Incremental Assignment Download

- **Method**: `GET`
- **Path**: `/inspections/sync/assignments/`
- **Query Parameters**:
  - `since` (ISO8601, optional): return assignments updated after this timestamp
  - `cursor` (opaque string, optional): pagination cursor
  - `limit` (int, optional, default 100, max 500)
  - `includeCompleted` (bool, optional, default false)

**Successful Response**

```json
{
  "success": true,
  "data": {
    "assignments": [
      {
        "id": "7af1b21d-2a3c-4f36-8b44-a890d2fb4b8f",
        "inspection": "b55c8a14-9bb0-4ee1-9124-4fb101f2f5c0",
        "assigned_to": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "assigned_team": "northern-region",
        "status": "assigned",
        "priority": "high",
        "due_at": "2025-10-01T07:30:00Z",
        "acknowledged_at": null,
        "completed_at": null,
        "workflow_flags": {
          "requires_qc": true,
          "photos_required": false
        },
        "server_updated_at": "2025-09-28T12:01:10Z",
        "last_transition_id": "9a3cfc47-a023-44fc-9f10-1ab449efece7"
      }
    ],
    "approvals": [
      {
        "id": "483c2a9a-4b09-4ab7-9b95-6edd5d159554",
        "assignment_id": "7af1b21d-2a3c-4f36-8b44-a890d2fb4b8f",
        "step_code": "team_lead",
        "decision": "pending",
        "actor_id": null,
        "decided_at": null,
        "requires_merge": false,
        "server_updated_at": "2025-09-28T12:01:10Z"
      }
    ],
    "next_cursor": "g2wAAAABaA==",
    "server_time": "2025-09-28T12:05:00Z"
  }
}
```

Notes:

- Response includes both assignments and approvals to keep client caches consistent.
- `server_time` is the authoritative timestamp for updating local `lastAssignmentsDownloadAt`.
- When `since` is omitted the server returns pending and in-progress assignments for the authenticated user.

### 2. Assignment Upload (Create/Update/Transition)

- **Method**: `POST`
- **Path**: `/inspections/sync/assignments/`

**Request Body**

```json
{
  "device_id": "device-123",
  "operations": [
    {
      "op": "create",
      "client_id": "temp-001",
      "payload": {
        "inspection": "b55c8a14-9bb0-4ee1-9124-4fb101f2f5c0",
        "assigned_to": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "priority": "medium",
        "due_at": "2025-10-02T08:00:00Z",
        "status": "assigned"
      },
      "client_updated_at": "2025-09-28T08:15:00Z"
    },
    {
      "op": "update",
      "id": "7af1b21d-2a3c-4f36-8b44-a890d2fb4b8f",
      "payload": {
        "priority": "high",
        "notes": "Emergency reschedule due to outage"
      },
      "client_updated_at": "2025-09-28T09:02:00Z",
      "expected_server_updated_at": "2025-09-28T12:01:10Z"
    },
    {
      "op": "transition",
      "id": "7af1b21d-2a3c-4f36-8b44-a890d2fb4b8f",
      "transition": "in_progress",
      "context": {
        "gps": {
          "lat": -17.8218,
          "lng": 31.0493
        }
      },
      "client_updated_at": "2025-09-28T09:05:10Z",
      "expected_server_updated_at": "2025-09-28T12:01:10Z"
    }
  ]
}
```

**Success Response**

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "client_id": "temp-001",
        "id": "e119b8f9-6b3f-48b0-a1ba-ec054d5a4976",
        "operation": "create",
        "server_updated_at": "2025-09-28T12:05:03Z"
      },
      {
        "id": "7af1b21d-2a3c-4f36-8b44-a890d2fb4b8f",
        "operation": "update",
        "server_updated_at": "2025-09-28T12:05:04Z"
      },
      {
        "id": "7af1b21d-2a3c-4f36-8b44-a890d2fb4b8f",
        "operation": "transition",
        "new_status": "in_progress",
        "transition_id": "6d03a3cd-7a0c-4668-936e-63d1d2d746b0",
        "server_updated_at": "2025-09-28T12:05:05Z"
      }
    ],
    "conflicts": []
  }
}
```

**Conflict Response Example**

```json
{
  "success": true,
  "data": {
    "results": [],
    "conflicts": [
      {
        "id": "7af1b21d-2a3c-4f36-8b44-a890d2fb4b8f",
        "reason": "stale_update",
        "server_payload": {
          "status": "completed",
          "server_updated_at": "2025-09-28T11:59:59Z",
          "completed_at": "2025-09-28T11:59:30Z"
        },
        "client_payload": {
          "status": "in_progress",
          "client_updated_at": "2025-09-28T09:05:10Z"
        },
        "resolution_endpoint": "/inspections/sync/assignments/conflicts/"
      }
    ]
  },
  "message": "1 conflict detected"
}
```

Server processes operations sequentially and stops on fatal validation errors. For each failure the response includes `errors` with an array of `{operationIndex, field, code, detail}` objects.

### 3. Approval Transition Upload

- **Method**: `POST`
- **Path**: `/inspections/sync/approvals/transitions/`

**Request Body**

```json
{
  "device_id": "device-123",
  "transitions": [
    {
      "approval_id": "483c2a9a-4b09-4ab7-9b95-6edd5d159554",
      "decision": "approved",
      "comment": "Reviewed photos, good to go",
      "actor_id": "9b005678-4f52-4a62-9db3-754b238f721f",
      "merge_context": {
        "requires_merge": false
      },
      "client_updated_at": "2025-09-28T12:02:00Z",
      "expected_server_updated_at": "2025-09-28T12:01:10Z"
    }
  ]
}
```

**Success Response** mirrors assignment upload, returning updated approvals and any conflicts (e.g. if another approver took action first).

### 4. Conflict Resolution Endpoint

- **Method**: `POST`
- **Path**: `/inspections/sync/assignments/conflicts/`

**Use Cases**

1. Accept server version (`resolution`: `take_server`)
2. Force client overwrite (`resolution`: `force_client`, requires elevated permissions)
3. Merge partial fields (`resolution`: `merge_fields`, supply `merged_payload`)

**Request Body**

```json
{
  "conflict_id": "c791da0c-2f0e-44ae-9d6f-25f9d4aa4741",
  "resolution": "merge_fields",
  "merged_payload": {
    "status": "completed",
    "completed_at": "2025-09-28T12:10:00Z",
    "notes": "Server photos retained, client comments merged"
  }
}
```

Server returns the reconciled assignment and updated `server_updated_at`. The mobile client clears `conflictState` for the assignment on success.

### 5. Merge Hook Notifications

Assignments or approvals that require manual merges (e.g. conflicting photo attachments or overlapping edits) should set `requires_merge = true` in approval payloads. A dedicated endpoint keeps the mobile client in sync with merge tasks:

- **Method**: `GET`
- **Path**: `/inspections/sync/assignments/merge-tasks/`
- **Query**: `status` (`pending`, `in_progress`, `resolved`)

Response contains merge tasks (`id`, `assignment_id`, `merge_type`, `created_at`, `assigned_to`, `status`, `resolution_due_at`). The mobile app shows merge prompts and can update status via a `PATCH /inspections/sync/assignments/merge-tasks/{id}/` endpoint.

## Mapper Helper Contracts (TypeScript)

Add/extend strongly typed helpers in `services/inspectionSyncService.ts`:

- `mapServerAssignmentToLocal(payload: ServerAssignment): LocalAssignment`
- `mapLocalAssignmentToUpload(op: AssignmentOperation): ServerAssignmentPayload`
- `mapServerApprovalToLocal(payload: ServerApproval): LocalApproval`
- `buildAssignmentConflict(local: LocalAssignment, server: ServerAssignment): AssignmentConflict`

Suggested interface sketches:

```ts
interface ServerAssignment {
  id: string;
  inspection: string;
  assigned_to: string;
  assigned_team?: string;
  status: AssignmentStatus;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  due_at?: string;
  acknowledged_at?: string | null;
  completed_at?: string | null;
  workflow_flags: Record<string, boolean>;
  server_updated_at: string;
  last_transition_id?: string;
}

interface LocalAssignment {
  id: string;
  inspectionId: string;
  assignedTo: string;
  assignedTeam?: string;
  status: AssignmentStatus;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  dueAt?: string;
  acknowledgedAt?: string | null;
  completedAt?: string | null;
  workflowFlags: Record<string, boolean>;
  serverUpdatedAt: string;
  localUpdatedAt: string;
  dirty: 0 | 1;
  conflictState?: string | null;
}
```

Ensure mapper helpers compute `payloadHash` deterministically (sorted keys, stable JSON stringify) so that conflict detection can highlight significant changes.

## Sync Metadata Handshake

Introduce a `GET /inspections/sync/assignments/handshake/` endpoint returning:

```json
{
  "success": true,
  "data": {
    "server_time": "2025-09-28T12:05:00Z",
    "max_page_size": 500,
    "supported_assignment_statuses": ["assigned", "acknowledged", "in_progress", "completed", "blocked", "rejected", "cancelled"],
    "supported_approval_decisions": ["pending", "approved", "rejected", "needs_changes", "auto_approved"],
    "supports_merge_hooks": true,
    "supports_conflict_resolution": true
  }
}
```

Mobile clients call this endpoint during app launch to seed dropdowns and feature toggles.

## Postman Collection Updates

Replace placeholder folders with concrete requests:

- `Assignments › Download Assignments` (GET) with query params, example response, tests verifying envelope shape
- `Assignments › Upload Assignments` (POST) including at least one create/update/transition operation
- `Assignments › Conflict Resolution` (POST) verifying `conflicts` array structure
- `Approvals › Submit Approval Transition` (POST)
- `Approvals › Fetch Pending Merge Tasks` (GET)

Each request should store `baseUrl` and `authToken` variables, referencing the same configuration block used across other inspection sync operations.

## Implementation Roadmap

1. **Backend (Django)**
   - Model migrations for `InspectionAssignment`, `AssignmentApproval`, `AssignmentSyncAudit`
   - DRF serializers and viewsets implementing the endpoints above
   - Conflict detection service comparing `expected_server_updated_at`
   - Merge task workflow with signals when approvals require merges

2. **Mobile Client**
   - Update `schema.ts` and migrations with new tables
   - Implement mapper helpers and local repositories for assignments and approvals
   - Extend `inspectionSyncService` with incremental download, upload, approval transitions, conflict resolution flows
   - Add UI for merge tasks/conflicts (htmx dashboards reference where applicable)

3. **Testing**
   - Backend unit tests for serializers, transitions, conflict service
   - API integration tests covering incremental sync and conflict scenarios
   - Mobile unit tests for mapper utilities and queue processing

4. **Documentation & Tooling**
   - Update Mobile Sync API spec to include assignments and approvals sections
   - Regenerate Postman collection (`ACE2/postman_collection.json`) with new endpoints
   - Add developer onboarding notes to `documentation/` (link this contract)

## Next Steps Checklist

- [ ] Review proposed contract with backend stakeholders
- [ ] Finalize field list and enums (especially workflow flags)
- [ ] Create Django models and migrations per contract
- [ ] Implement DRF endpoints and conflict service
- [ ] Wire endpoints into `apiEndpoints.ts`
- [ ] Update mobile schema and mapper helpers
- [ ] Refresh Postman collection with working requests
- [ ] Run sync service unit/integration tests once implementations land

Once approved, this contract becomes the single source of truth for assignment sync features and should be referenced by both backend and mobile teams during implementation.


