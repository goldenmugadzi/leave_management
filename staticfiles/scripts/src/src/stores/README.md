# Schedule Zustand Store

This directory contains the Zustand store implementation for managing schedule-related state, replacing the previous Context API approach.

## Overview

The store provides centralized state management for all schedule-related data including:
- Basic schedule information (CS ID, creator, dates, etc.)
- PR data and items
- Bid management
- Compliance and committee data
- Approval workflow
- File management
- Loading states and validation

## Store Structure

### Core State
- **Basic Schedule Data**: CS ID, creator, dates, owner information
- **Reference Data**: Suppliers, users, currencies, procurement plans
- **PR Data**: Purchase request information and items
- **Bid Management**: Current bids, bid count, modal states
- **Compliance**: Compliance data and remarks
- **Committee**: Committee members and their status
- **Approvals**: GM/FM approval workflow
- **UI State**: Loading states, active tabs, validation errors

### Actions
- **Setters**: Individual state setters for each field
- **Data Actions**: CRUD operations for PR data, bids, compliance
- **Computed Actions**: Business logic functions like `isCreator()`, `checkApprovalsComplete()`
- **Reset Actions**: Functions to clear specific parts of the store
- **Batch Actions**: Bulk operations for initialization and updates

## Usage

### Basic Store Usage
```typescript
import { useScheduleStore } from '../stores/scheduleStore';

const MyComponent = () => {
  const { csId, setCsId, isLoading } = useScheduleStore();
  
  const handleUpdate = () => {
    setCsId('CS-2024-001');
  };
  
  return (
    <div>
      <p>CS ID: {csId}</p>
      <button onClick={handleUpdate}>Update</button>
      {isLoading && <p>Loading...</p>}
    </div>
  );
};
```

### Using Selectors for Performance
```typescript
import { useScheduleSelector } from '../stores/scheduleStore';

const MyComponent = () => {
  // Only re-renders when csId or username changes
  const { csId, username } = useScheduleSelector(state => ({
    csId: state.csId,
    username: state.username
  }));
  
  return (
    <div>
      <p>CS ID: {csId}</p>
      <p>Username: {username}</p>
    </div>
  );
};
```

### Using Pre-built Selectors
```typescript
import { useScheduleBids, useSchedulePermissions } from '../stores/scheduleStore';

const BidsComponent = () => {
  const { bids, bidCount } = useScheduleBids();
  const { isCreator } = useSchedulePermissions();
  
  return (
    <div>
      <h3>Bids ({bidCount})</h3>
      {isCreator && <button>Add Bid</button>}
      {bids.map(bid => (
        <div key={bid.bid_count}>{bid.supplier_name}</div>
      ))}
    </div>
  );
};
```

## Key Features

### 1. Persistence
- Non-sensitive data is automatically persisted to localStorage
- Sensitive data (bids, compliance, etc.) is not persisted for security

### 2. DevTools Integration
- Full Redux DevTools support for debugging
- Store name: 'schedule-store'

### 3. Type Safety
- Full TypeScript support with comprehensive interfaces
- All actions and state are properly typed

### 4. Performance Optimizations
- Selective re-rendering with custom selectors
- Memoized selectors for expensive computations
- Efficient state updates with immutable patterns

### 5. Business Logic
- Built-in computed actions for common business rules
- Centralized validation and permission checking
- Consistent state update patterns

## Migration from Context API

### Before (Context API)
```typescript
import { useScheduleContext } from '../context/ScheduleContext';

const MyComponent = () => {
  const { csId, setCsId } = useScheduleContext();
  // Component re-renders on ANY context change
};
```

### After (Zustand)
```typescript
import { useScheduleStore, useScheduleSelector } from '../stores/scheduleStore';

const MyComponent = () => {
  // Only re-renders when csId changes
  const { csId, setCsId } = useScheduleSelector(state => ({
    csId: state.csId,
    setCsId: state.setCsId
  }));
};
```

## Testing

The store includes comprehensive tests in `__tests__/scheduleStore.test.ts` covering:
- Basic setter actions
- Data management actions
- Computed actions
- Reset functionality
- Batch operations

## Demo Component

Use `StoreDemo.tsx` to test the store functionality in development:
```typescript
import { StoreDemo } from '../stores';

// In your app
<StoreDemo />
```

## Best Practices

1. **Use Selectors**: Always use `useScheduleSelector` instead of accessing the full store
2. **Minimize Re-renders**: Only select the state you actually need
3. **Use Pre-built Selectors**: Leverage the provided selector hooks for common patterns
4. **Batch Updates**: Use `updateScheduleData` for multiple related updates
5. **Reset When Needed**: Use reset functions to clear state between different schedules

## Future Enhancements

- Add middleware for logging and analytics
- Implement undo/redo functionality
- Add optimistic updates for better UX
- Create action creators for complex operations
- Add state synchronization between tabs
