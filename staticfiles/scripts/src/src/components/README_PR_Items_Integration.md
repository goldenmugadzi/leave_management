# PR Items Management Tab Integration

This document explains how to integrate the new PR Items Management tab into the existing Schedule component.

## Overview

The PR Items Management has been moved to a separate tab that becomes available only after the schedule details have been successfully saved. This improves the user experience by:

1. Ensuring required schedule details are saved first
2. Providing a focused interface for PR items management
3. Separating concerns between schedule creation and PR items selection

## Backend Changes

### New API Endpoints

1. **`/api/cs-pr-items-management/<cs_id>/`** (GET)
   - Returns PR items data for management tab
   - Only accessible after CS details are saved
   - Returns items categorized as: selected, available, or used in other schedules

2. **`/api/cs-pr-items-update/<cs_id>/`** (POST)
   - Updates PR items selection for a CS
   - Accepts JSON data with item selections
   - Returns statistics on added/removed items

### Modified Functions

1. **`get_comperative_schedule_data`**
   - No longer includes PR items in main data load
   - Returns `pr_items_tab_enabled` and `has_pr_items_configured` flags

2. **`save_comparative_schedule`** and **`update_comparative_schedule`**
   - Now return `pr_items_tab_enabled: true` after successful save
   - Include `redirect_to_pr_items: true` for new schedules

## Frontend Integration

### 1. Import the Component

```tsx
import PrItemsManager from './PrItemsManager';
```

### 2. Add State for Tab Management

```tsx
const [scheduleData, setScheduleData] = useState({
  pr_items_tab_enabled: false,
  has_pr_items_configured: false,
  // ... other schedule data
});
```

### 3. Update Tab Configuration

```tsx
const TAB_CONFIG = [
  { id: 'details', label: 'Details', icon: '📄' },
  { 
    id: 'pr-items', 
    label: 'PR Items', 
    icon: '📋',
    disabled: !scheduleData.pr_items_tab_enabled,
    indicator: scheduleData.pr_items_tab_enabled && !scheduleData.has_pr_items_configured
  },
  { id: 'bids', label: 'Supplier Bids', icon: '💰', disabled: !scheduleData.pr_items_tab_enabled },
  // ... other tabs
];
```

### 4. Add Tab Content

```tsx
// In your tab rendering logic
{activeTab === 'pr-items' && (
  <PrItemsManager
    csId={csId}
    enabled={scheduleData.pr_items_tab_enabled}
    onItemsUpdated={(stats) => {
      setScheduleData(prev => ({
        ...prev,
        has_pr_items_configured: stats.total > 0
      }));
      // Optionally show success message
      console.log(`Updated: ${stats.added} added, ${stats.removed} removed`);
    }}
  />
)}
```

### 5. Handle Save Success

```tsx
const handleSaveScheduleDetails = async (formData) => {
  try {
    const response = await fetch('/comperative_schedule/save', {
      method: 'POST',
      body: formData,
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Update schedule data with new flags
      setScheduleData(prev => ({
        ...prev,
        cs_id: result.cs_id,
        pr_items_tab_enabled: result.pr_items_tab_enabled,
      }));

      // Automatically switch to PR items tab for new schedules
      if (result.redirect_to_pr_items) {
        setActiveTab('pr-items');
      }
    }
  } catch (error) {
    console.error('Error saving schedule:', error);
  }
};
```

## User Flow

1. **Create New Schedule**
   - User fills in schedule details
   - Saves schedule details
   - System automatically enables PR Items tab
   - User is prompted/redirected to configure PR items

2. **Edit Existing Schedule**
   - User opens existing schedule
   - PR Items tab is enabled if schedule has CS ID
   - Tab shows indicator if PR items haven't been configured
   - User can modify PR items selection

3. **PR Items Management**
   - Shows all PR items with their current status
   - Color-coded items: green (selected), orange (used elsewhere), blue (available)
   - Disabled items cannot be selected (already used in other schedules)
   - Save updates the selection and clears approvals if needed

## Visual Indicators

- **Tab Badge**: Orange dot indicator when PR items need configuration
- **Item Status Colors**:
  - Green: Selected for this CS
  - Orange: Used in other schedules (disabled)
  - Blue: Available for selection
- **Summary Stats**: Shows selected/available/total counts

## API Response Examples

### PR Items Management Data
```json
{
  "success": true,
  "cs_id": "CS20241201120000",
  "pr_id": "PR123",
  "pr_number": "PR123",
  "pr_items": [
    {
      "id": "1",
      "item_required": "Office Chairs",
      "quantity": 10,
      "unit_of_measurement": "Each",
      "status": "selected_for_this_cs",
      "included": true,
      "source": "cs_required_items"
    },
    {
      "id": "2",
      "item_required": "Desks",
      "quantity": 5,
      "unit_of_measurement": "Each",
      "status": "available",
      "included": false,
      "source": "pr_items"
    }
  ],
  "total_items": 2,
  "selected_items": 1,
  "available_items": 1,
  "can_modify": true
}
```

### Update Response
```json
{
  "success": true,
  "message": "PR Items updated successfully",
  "stats": {
    "added_items": 2,
    "removed_items": 1,
    "total_selected": 3
  }
}
```

## Benefits

1. **Better UX**: Clear separation of concerns, guided workflow
2. **Data Integrity**: Ensures schedule details are saved before items management
3. **Performance**: Lazy loading of PR items data only when needed
4. **Flexibility**: Easy to extend with additional item management features
5. **Validation**: Clear feedback on item availability and conflicts

## Next Steps

1. Add validation for minimum items requirement
2. Implement bulk selection/deselection
3. Add search and filtering for large item lists
4. Include item modification history
5. Add export functionality for selected items 