# Mobile App Integration Guide for Inspection Sync

## Overview

This guide provides step-by-step instructions for integrating the BEApp mobile application with the Django backend sync system. The sync system enables offline-first functionality with robust conflict resolution.

## Prerequisites

- Mobile app with network connectivity
- JWT authentication system
- Local storage for offline data
- Background task processing capability

## 1. Authentication Setup

### 1.1 Get JWT Token

First, authenticate the user and obtain a JWT token:

```typescript
const loginResponse = await fetch('/api/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password123'
  })
});

const { access, refresh } = await loginResponse.json();
```

### 1.2 Configure Sync Service

Initialize the sync service with the JWT token:

```typescript
import { SyncService } from './services/SyncService';

const syncService = new SyncService({
  baseUrl: 'https://api.example.com/inspections/sync',
  token: access,
  timeout: 30000,
  retries: 3
});
```

## 2. Initial Setup and Full Sync

### 2.1 Perform Initial Full Sync

When the app launches for the first time or after a long offline period:

```typescript
try {
  const result = await syncService.performFullSync();

  if (result.success) {
    console.log(`Downloaded ${result.records_processed} records`);
    // Update local database with downloaded data
    await updateLocalDatabase(result.data);
  } else {
    console.error('Full sync failed:', result.errors);
  }
} catch (error) {
  console.error('Network error during full sync:', error);
  // Handle offline mode
}
```

### 2.2 Set Up Periodic Sync

Configure automatic background sync:

```typescript
// Sync every 15 minutes when online
setInterval(async () => {
  if (navigator.onLine) {
    const lastSyncTime = await getLastSyncTimestamp();
    await syncService.performIncrementalSync(lastSyncTime);
  }
}, 15 * 60 * 1000);

// Sync when app resumes from background
document.addEventListener('visibilitychange', async () => {
  if (!document.hidden && navigator.onLine) {
    const lastSyncTime = await getLastSyncTimestamp();
    await syncService.performIncrementalSync(lastSyncTime);
  }
});
```

## 3. Inspection Data Operations

### 3.1 Creating New Inspections

When creating a new inspection in the mobile app:

```typescript
const inspectionData = {
  consumer_name: "John Smith",
  inspection_date: "2025-01-15",
  service_no: "SVC-001",
  status: "pending",
  client_application_id: applicationId,
  // ... other fields
};

try {
  const result = await syncService.syncInspection(inspectionData);

  if (result.success) {
    // Update local database with server response
    await saveInspectionLocally({
      id: result.inspection_id,
      ...inspectionData,
      sync_status: 'synced'
    });

    console.log('Inspection created successfully');
  } else {
    // Handle validation errors
    if (result.errors) {
      showValidationErrors(result.errors);
    }

    // Store for later sync if offline
    await queueForSync(inspectionData);
  }
} catch (error) {
  // Network error - queue for later
  await queueForSync(inspectionData);
}
```

### 3.2 Updating Existing Inspections

When updating an inspection:

```typescript
const updatedData = {
  id: inspectionId,
  consumer_name: "John Smith Updated",
  status: "in_progress",
  all_equipment_bonded_earthed: "pass",
  // ... other changed fields
};

const result = await syncService.syncInspection(updatedData);

if (result.success) {
  await updateLocalInspection(result.inspection_id, updatedData);
} else {
  await handleSyncError(result);
}
```

### 3.3 Batch Operations

For better performance with multiple inspections:

```typescript
const inspectionsToSync = [
  { /* inspection 1 data */ },
  { /* inspection 2 data */ },
  { /* inspection 3 data */ }
];

const result = await syncService.syncInspectionBatch(inspectionsToSync);

if (result.success) {
  console.log(`Synced ${result.results.successful} inspections`);
} else {
  // Handle partial failures
  result.results.errors.forEach(error => {
    console.error(`Inspection ${error.index} failed:`, error.errors);
  });
}
```

## 4. Conflict Resolution

### 4.1 Automatic Resolution

The system automatically resolves most conflicts using business rules:

```typescript
// The sync service handles this internally
const syncResult = await syncService.performIncrementalSync(lastSyncTime);

// Check if conflicts were auto-resolved
if (syncResult.conflicts_resolved > 0) {
  console.log(`${syncResult.conflicts_resolved} conflicts auto-resolved`);
}
```

### 4.2 Manual Resolution

For conflicts requiring user intervention:

```typescript
// 1. Get unresolved conflicts
const conflicts = await syncService.getConflicts();

// 2. Show resolution UI for each conflict
for (const conflict of conflicts) {
  const resolution = await showConflictResolutionUI(conflict);

  // 3. Submit resolution
  const resolveResult = await syncService.resolveConflict(
    conflict.id,
    resolution.type,
    resolution.data
  );

  if (resolveResult.success) {
    console.log('Conflict resolved successfully');
  }
}
```

## 5. Offline Queue Management

### 5.1 Queue Operations When Offline

```typescript
class OfflineQueue {
  private queue: QueuedOperation[] = [];

  async add(operation: Omit<QueuedOperation, 'id' | 'created_at' | 'attempts'>) {
    const queuedOperation: QueuedOperation = {
      id: generateId(),
      created_at: new Date().toISOString(),
      attempts: 0,
      ...operation
    };

    this.queue.push(queuedOperation);
    await this.saveToStorage();
  }

  async process() {
    if (!navigator.onLine) return;

    const operations = await this.getPendingOperations();

    for (const operation of operations) {
      try {
        await this.executeOperation(operation);
        await this.remove(operation.id);
      } catch (error) {
        operation.attempts++;

        if (operation.attempts >= operation.max_attempts) {
          await this.markAsFailed(operation.id, error);
        } else {
          await this.scheduleRetry(operation);
        }
      }
    }
  }

  private async executeOperation(operation: QueuedOperation) {
    switch (operation.type) {
      case 'inspection_create':
        return syncService.syncInspection(operation.data);
      case 'inspection_update':
        return syncService.syncInspection(operation.data);
      default:
        throw new Error(`Unknown operation type: ${operation.type}`);
    }
  }
}
```

### 5.2 Network Status Handling

```typescript
// Monitor network status
window.addEventListener('online', async () => {
  console.log('Back online - processing sync queue');
  await offlineQueue.process();
});

window.addEventListener('offline', () => {
  console.log('Gone offline - operations will be queued');
});
```

## 6. Error Handling and Retry Logic

### 6.1 Retry Configuration

```typescript
const RETRY_CONFIG = {
  maxAttempts: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 30000, // 30 seconds
  backoffMultiplier: 2
};

async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  config = RETRY_CONFIG
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < config.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      if (attempt < config.maxAttempts - 1) {
        const delay = Math.min(
          config.baseDelay * Math.pow(config.backoffMultiplier, attempt),
          config.maxDelay
        );

        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError!;
}
```

### 6.2 Error Classification

```typescript
function classifyError(error: any): 'network' | 'validation' | 'conflict' | 'server' {
  if (error.name === 'NetworkError' || error.status === 0) {
    return 'network';
  }

  if (error.status === 400) {
    return 'validation';
  }

  if (error.status === 422) {
    return 'conflict';
  }

  if (error.status >= 500) {
    return 'server';
  }

  return 'network';
}

async function handleSyncError(error: any, operation: any) {
  const errorType = classifyError(error);

  switch (errorType) {
    case 'network':
      // Queue for retry when online
      await offlineQueue.add(operation);
      break;

    case 'validation':
      // Show validation errors to user
      showValidationErrors(error.errors);
      break;

    case 'conflict':
      // Handle conflict resolution
      await handleConflict(error.conflict);
      break;

    case 'server':
      // Server error - queue for retry
      await offlineQueue.add(operation);
      break;
  }
}
```

## 7. Real-time Updates

### 7.1 WebSocket Integration (Future)

```typescript
// For real-time sync updates (when implemented)
const websocket = new WebSocket('wss://api.example.com/ws/sync/');

websocket.onmessage = (event) => {
  const update = JSON.parse(event.data);

  switch (update.type) {
    case 'inspection_updated':
      handleRealTimeInspectionUpdate(update.data);
      break;
    case 'conflict_detected':
      handleRealTimeConflict(update.data);
      break;
  }
};
```

## 8. Data Synchronization Strategy

### 8.1 Sync Intervals

```typescript
const SYNC_INTERVALS = {
  full: 24 * 60 * 60 * 1000,      // 24 hours
  incremental: 15 * 60 * 1000,     // 15 minutes
  critical: 60 * 1000,             // 1 minute (for urgent updates)
  conflict_check: 5 * 60 * 1000    // 5 minutes
};
```

### 8.2 Smart Sync Strategy

```typescript
class SmartSyncManager {
  async shouldPerformFullSync(): Promise<boolean> {
    const lastFullSync = await getLastFullSyncTime();
    const timeSinceLastSync = Date.now() - lastFullSync;

    return timeSinceLastSync > SYNC_INTERVALS.full;
  }

  async determineSyncType(): Promise<'full' | 'incremental'> {
    if (await this.shouldPerformFullSync()) {
      return 'full';
    }

    const pendingOperations = await getPendingOperationsCount();
    return pendingOperations > 10 ? 'full' : 'incremental';
  }

  async performSmartSync() {
    const syncType = await this.determineSyncType();
    const lastSyncTime = await getLastSyncTimestamp();

    if (syncType === 'full') {
      return syncService.performFullSync();
    } else {
      return syncService.performIncrementalSync(lastSyncTime);
    }
  }
}
```

## 9. Testing and Debugging

### 9.1 Test Data Setup

```typescript
// Create test inspection data
const testInspection = {
  consumer_name: "Test Consumer",
  inspection_date: new Date().toISOString().split('T')[0],
  service_no: `TEST-${Date.now()}`,
  status: "pending",
  client_application_id: testApplicationId,
  all_equipment_bonded_earthed: "pass",
  socket_outlets_earthed: "pass",
  circuit_conductors_correct_size: "pass"
};

// Test sync operation
const testResult = await syncService.syncInspection(testInspection);
console.log('Test sync result:', testResult);
```

### 9.2 Debug Logging

```typescript
// Enable detailed logging
syncService.enableDebugLogging();

// Log sync operations
console.log('Sync operation started:', {
  timestamp: new Date().toISOString(),
  operation: 'inspection_sync',
  data: inspectionData
});
```

## 10. Performance Optimization

### 10.1 Batch Size Optimization

```typescript
const OPTIMAL_BATCH_SIZES = {
  inspections: 10,
  photos: 5,
  conflicts: 20
};

async function syncInspectionsOptimally(inspections: any[]) {
  const batches = chunkArray(inspections, OPTIMAL_BATCH_SIZES.inspections);

  for (const batch of batches) {
    await syncService.syncInspectionBatch(batch);

    // Small delay between batches to prevent overwhelming the server
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}
```

### 10.2 Memory Management

```typescript
class MemoryManager {
  private maxCacheSize = 50 * 1024 * 1024; // 50MB
  private currentCacheSize = 0;

  async addToCache(key: string, data: any) {
    const dataSize = JSON.stringify(data).length;

    if (this.currentCacheSize + dataSize > this.maxCacheSize) {
      await this.evictOldCacheEntries(dataSize);
    }

    this.currentCacheSize += dataSize;
    await setCachedData(key, data);
  }

  private async evictOldCacheEntries(requiredSpace: number) {
    const entries = await getAllCacheEntries();
    const sortedByAge = entries.sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    let freedSpace = 0;
    for (const entry of sortedByAge) {
      await removeCacheEntry(entry.key);
      freedSpace += entry.size;

      if (freedSpace >= requiredSpace) break;
    }

    this.currentCacheSize -= freedSpace;
  }
}
```

## 11. Security Considerations

### 11.1 Token Management

```typescript
class TokenManager {
  private refreshThreshold = 5 * 60 * 1000; // 5 minutes

  async getValidToken(): Promise<string> {
    const token = await getStoredToken();
    const expiresAt = getTokenExpirationTime(token);

    if (Date.now() > expiresAt - this.refreshThreshold) {
      return this.refreshToken();
    }

    return token;
  }

  private async refreshToken(): Promise<string> {
    const refreshToken = await getStoredRefreshToken();

    const response = await fetch('/api/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });

    const { access } = await response.json();
    await storeToken(access);

    return access;
  }
}
```

### 11.2 Data Encryption

```typescript
// Encrypt sensitive data before storing locally
const encryptedData = await encryptData(inspectionData, encryptionKey);
await storeLocally('inspections', encryptedData);

// Decrypt when needed
const decryptedData = await decryptData(storedData, encryptionKey);
```

## 12. Deployment Checklist

- [ ] JWT authentication working
- [ ] Sync service initialized with correct base URL
- [ ] Offline queue implemented
- [ ] Conflict resolution UI implemented
- [ ] Error handling and retry logic tested
- [ ] Performance optimization applied
- [ ] Security measures implemented
- [ ] Testing with real API completed
- [ ] Documentation provided to users

## Support

For technical support:
- Check the API logs in Django admin
- Review sync operation history
- Contact backend development team for API issues
- Use the provided Postman collection for testing

---

*This integration guide will be updated as the sync system evolves.*
