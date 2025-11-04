# Sync Strategy Analysis: E117 vs E1/E6

## Executive Summary

**E117 inspections sync successfully** while **E1 defect reports and E6 certificates fail** with a 500 error. The root cause is a serializer field mismatch: the serializers include a `status` field that doesn't exist in the Django models for E1DefectReport and E6Certificate.

## What Works: E117 Inspection Sync

### Strategy Overview
E117 inspections use a **direct upload approach** with proper field mapping and validation.

### Key Components

1. **Endpoint**: `/inspections/api/sync/mobile-sync-inspection/`
2. **Method**: POST
3. **Serializer**: `InspectionReportSyncSerializer`
4. **Model**: `InspectionReport` (has `status` field ✓)

### Working Flow

```
Mobile App → transformToBackendFormat() → POST /mobile-sync-inspection/
  ↓
Backend receives payload with all fields including 'status'
  ↓
Serializer validates → Model.save() succeeds (status field exists)
  ↓
Returns 201 Created or 200 Updated
```

### Key Success Factors

1. **Model-Serializer Alignment**: 
   - `InspectionReport` model HAS `status` field
   - `InspectionReportSyncSerializer` includes `status` in fields list
   - ✅ No mismatch

2. **Field Mapping**:
   - Mobile app sends fields in snake_case format
   - Serializer handles field name transformations correctly
   - All required fields are present

3. **Create/Update Logic**:
   - Backend checks for existing record by UUID `id`
   - Falls back to `service_no` or `mobile_id` lookup
   - Handles both create (201) and update (200) scenarios

4. **Payload Structure**:
   ```json
   {
     "id": "uuid-if-exists",
     "mobile_id": "local-id",
     "service_no": "...",
     "status": "pass|pending|fail",
     "consumer_name": "...",
     ...
   }
   ```

### Example Successful Sync
From logs:
```
✅ [UPLOAD SUCCESS] e117Inspections:e117_1761726882967_hozu5m6l0 
   → Server ID: 2eb941b0-7390-48f4-88e6-87b66c681c59
✅ [SYNC STATUS] Updated e117_1761726882967_hozu5m6l0 → synced
```

---

## What's Broken: E1 Defect Report Sync

### Strategy Overview
E1 defect reports use a **dependent upload approach** (requires inspection to be synced first), but fail due to serializer field mismatch.

### Key Components

1. **Endpoint**: `/inspections/api/sync/defects/e1/`
2. **Method**: POST
3. **Serializer**: `E1DefectReportSyncSerializer`
4. **Model**: `E1DefectReport` (does NOT have `status` field ✗)

### Failed Flow

```
Mobile App → transformToBackendFormat() → POST /defects/e1/
  ↓
Backend receives payload
  ↓
Serializer tries to validate → ERROR: 'status' field not in model
  ↓
500 Internal Server Error: "Field name `status` is not valid for model `E1DefectReport`"
```

### Root Cause

**Serializer-Model Mismatch**:
- `E1DefectReportSyncSerializer` includes `'status'` in fields list (line 220)
- `E1DefectReport` model does NOT have a `status` field
- Django REST Framework raises error when serializer field doesn't match model

### Error Details

```
ERROR ❌ [SERVER ERROR] POST /inspections/api/sync/defects/e1/ - 500
Error: Field name `status` is not valid for model `E1DefectReport` 
       in `inspections.sync_serializers.E1DefectReportSyncSerializer`.
```

### Fix Applied

✅ **Removed `status` field from `E1DefectReportSyncSerializer`**

The serializer now correctly only includes fields that exist in the model:
- `id`, `inspection_id`, `report_number`, `defects_list`, etc.
- `created_at`, `updated_at`
- Computed fields via `SerializerMethodField`

---

## What's Broken: E6 Certificate Sync

### Strategy Overview
E6 certificates use the same approach as E1, but also fail due to the same serializer field mismatch.

### Key Components

1. **Endpoint**: `/inspections/api/sync/certificates/e6/`
2. **Method**: POST
3. **Serializer**: `E6CertificateSyncSerializer`
4. **Model**: `E6Certificate` (does NOT have `status` field ✗)

### Root Cause

Same issue as E1:
- `E6CertificateSyncSerializer` includes `'status'` in fields list (line 314)
- `E6Certificate` model does NOT have a `status` field

### Fix Applied

✅ **Removed `status` field from `E6CertificateSyncSerializer`**

---

## Comparison Table

| Aspect | E117 Inspection | E1 Defect Report | E6 Certificate |
|--------|----------------|------------------|----------------|
| **Status** | ✅ Working | ❌ Broken (fixed) | ❌ Broken (fixed) |
| **Model has `status` field** | ✅ Yes | ❌ No | ❌ No |
| **Serializer includes `status`** | ✅ Yes (correct) | ❌ Was yes (wrong) | ❌ Was yes (wrong) |
| **Dependency** | None (standalone) | Requires inspection synced | Requires inspection synced |
| **Endpoint** | `/mobile-sync-inspection/` | `/defects/e1/` | `/certificates/e6/` |
| **Create/Update Logic** | ✅ By UUID/service_no/mobile_id | ✅ By UUID | ✅ By UUID |

---

## Key Differences in Sync Strategy

### 1. **Field Mapping Strategy**

**E117**:
- Maps all fields directly from local to server format
- Includes computed fields via `SerializerMethodField`
- Handles field name transformations in `to_representation()`

**E1/E6**:
- Uses `SerializerMethodField` for computed values
- Relies on relationship fields (`inspection_report.id`, etc.)
- ❌ **Had incorrect `status` field** (now fixed)

### 2. **Upload Dependency**

**E117**:
- Standalone upload
- No dependencies

**E1/E6**:
- Requires parent inspection to be synced first
- Must provide `inspection_report_id` (server UUID)
- Validates inspection exists before saving

### 3. **Error Handling**

**E117**:
- Handles duplicate entries gracefully
- Marks as synced if duplicate detected
- Provides clear error messages

**E1/E6**:
- Now fixed - no longer fails on serializer validation
- Still requires proper error handling for missing inspection

---

## Mobile App Upload Strategy

### E117 Upload Flow (Working)

```typescript
// beapp/src/services/inspections/core/inspectionSyncService.ts
async uploadE117InspectionToServer(inspectionId: string) {
  1. Fetch inspection from local DB
  2. Validate inspection data
  3. Transform to server format (mapLocalToServerE117Inspection)
  4. POST to /mobile-sync-inspection/
  5. Update local record with server ID
}
```

### E1 Upload Flow (Now Fixed)

```typescript
// beapp/src/services/inspections/e1/defectReportUploadService.ts
async uploadE1DefectReport(reportId: string) {
  1. Fetch defect report from local DB
  2. Fetch linked inspection
  3. Check inspection.serverInspectionId exists
  4. Transform to backend format (transformToBackendFormat)
  5. POST to /defects/e1/
  6. Update local record with server ID
}
```

**Key Difference**: E1 requires `inspection.serverInspectionId` to be set (inspection must be synced first).

---

## Fixes Applied

### 1. E1DefectReportSyncSerializer
- ✅ Removed `'status'` from fields list
- ✅ Added comment explaining removal

### 2. E6CertificateSyncSerializer  
- ✅ Removed `'status'` from fields list
- ✅ Added comment explaining removal

---

## Recommendations

### 1. **One-by-One Sync Strategy**
The current approach syncs inspections one-by-one, which is correct. Ensure:
- ✅ E117 inspections sync first (standalone)
- ✅ E1 defects sync after their parent inspection is synced
- ✅ E6 certificates sync after their parent inspection is synced

### 2. **Field Validation**
- ✅ Always verify serializer fields match model fields
- ✅ Use Django's `model_fields` introspection to validate
- ✅ Add unit tests to catch serializer-model mismatches

### 3. **Error Messages**
- ✅ Improve error messages to indicate missing dependencies
- ✅ Provide clear guidance on sync order

### 4. **Testing**
- ✅ Test E1 defect upload after fix
- ✅ Test E6 certificate upload after fix
- ✅ Verify one-by-one sync workflow

---

## Next Steps

1. ✅ **Fixed**: Removed `status` field from E1 and E6 serializers
2. **Test**: Verify E1 defect upload works
3. **Test**: Verify E6 certificate upload works  
4. **Monitor**: Check logs for successful syncs
5. **Verify**: Confirm all records sync one-by-one correctly

---

## Summary

**E117 works because**:
- Model and serializer are aligned
- Field mapping is correct
- No dependencies

**E1/E6 were broken because**:
- Serializer included non-existent `status` field
- Fixed by removing `status` from serializer fields

**After fix**:
- E1 and E6 should sync successfully following the same pattern as E117
- One-by-one sync strategy remains intact

