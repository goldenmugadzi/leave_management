# How to Use the Fault Priority Change Feature

## Overview
This feature allows users who created faults to change the priority level of those faults, as long as they haven't been closed or resolved.

## Who Can Use This Feature
- **Fault Creators**: Only the person who originally reported the fault can change its priority
- **Active Faults Only**: Priority can only be changed for faults that are not closed or resolved

## How to Change Fault Priority

### Method 1: From the Fault List
1. Navigate to the fault list page (`/fault_locator/faults/`)
2. Find the fault you created (you'll see a "Change Priority" button)
3. Click the purple "🔄 Change Priority" button
4. Select the new priority level from the dropdown
5. Click "🔄 Change Priority" to save

### Method 2: From the Fault Detail/Update Page
1. Navigate to the fault detail page (`/fault_locator/faults/{fault_id}/`)
2. If you created the fault, you'll see a "🔄 Change Priority" button
3. Click the button to go to the priority change form
4. Select the new priority level and save

## Priority Levels Explained

| Level | Name | Color | Description |
|-------|------|-------|-------------|
| 1 | Low | Blue | Routine maintenance, no immediate impact |
| 2 | Medium | Green | Affects operations but not critical |
| 3 | High | Yellow | Urgent attention needed, impacts performance |
| 4 | Critical | Red | Immediate action required, serious impact |

## What Happens When You Change Priority

### Notifications Sent To:
- **Depot Forepersons** at the fault location
- **Senior Forepersons** (if priority is High or Critical)
- **Assigned Team Members** (if fault is currently assigned)

### Notification Content:
- Details about the priority change
- Who made the change and when
- Complete fault information
- Next steps guidance

### System Tracking:
- The system records who changed the priority (`prioritized_by`)
- The exact time of the change (`prioritized_at`)
- Full audit trail for accountability

## Important Notes

### Restrictions:
- ❌ You cannot change priority for faults you didn't create
- ❌ You cannot change priority for closed or resolved faults
- ❌ Only one priority change per fault update (not bulk changes)

### Best Practices:
- ✅ Change priority immediately if situation changes
- ✅ Consider the impact on other users before increasing priority
- ✅ Use appropriate priority levels (don't mark everything as Critical)
- ✅ Monitor notifications after high priority changes

## User Interface Features

### Visual Indicators:
- Priority badges with color coding throughout the interface
- Clear priority level descriptions with examples
- Warning messages for restrictions

### Responsive Design:
- Works on mobile devices and tablets
- Touch-friendly buttons and forms
- Optimized for field workers

## Troubleshooting

### Common Issues:

**"You can only change priority for faults you created"**
- This fault was created by someone else
- Only the original fault reporter can change priority

**"Priority cannot be changed for closed or resolved faults"**
- This fault has been completed and locked
- Contact a senior foreperson if changes are needed

**"Change Priority button not visible"**
- You may not be the fault creator
- The fault may be in a closed state
- Check your permissions with system administrator

## Technical Integration

### For Developers:
- View: `fault_locator.views.change_fault_priority`
- URL: `faults/<int:fault_id>/change-priority/`
- Template: `fault_locator/change_priority.html`
- Form: `FaultPriorityForm`
- Notification: `notify_priority_change` function

### Database Impact:
- Updates `fault.priority` field
- Sets `fault.prioritized_by` to current user
- Sets `fault.prioritized_at` to current timestamp
- Creates notification records for relevant users

## Support
For technical support or questions about this feature, contact your system administrator or IT support team.
