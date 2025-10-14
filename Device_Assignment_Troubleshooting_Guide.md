# Device Assignment Troubleshooting Guide

## Issue: No Devices Available for Assignment

### Problem
When trying to assign devices to teams, the device dropdown is empty or shows "---------" with no selectable options.

### Root Cause
All available devices are already assigned to teams. The form only shows unassigned devices.

### Solution

#### Option 1: Create New Devices
```bash
# Create a single device
python manage.py manage_devices --action create --serial "FLD-006" --description "New Device"

# Create multiple sample devices
python manage.py manage_devices --action create-sample
```

#### Option 2: Unassign Unused Devices
```bash
# List current device assignments
python manage.py manage_devices --action list

# Unassign all devices (use with caution)
python manage.py manage_devices --action unassign-all
```

#### Option 3: Manual Device Management
1. Go to Device Management in the fault locator dashboard
2. View device details to see current assignments
3. Unassign devices from teams that don't need them
4. Create new devices as needed

### Checking Device Status
Run the debug script to check device availability:
```bash
python debug_device_assignment.py
```

### Current Device Status
As of the latest check:
- Total devices: 6
- Available devices: 3 (FLD-001, FLD-002, FLD-003)
- Assigned devices: 3 (already assigned to teams)

### Prevention
1. **Create More Devices**: Keep a pool of unassigned devices for flexibility
2. **Regular Monitoring**: Check device assignments periodically
3. **Team Planning**: Plan device needs before creating teams

### Device Management Commands
```bash
# List all devices and their status
python manage.py manage_devices --action list

# Create a new device
python manage.py manage_devices --action create --serial "DEVICE_ID" --description "Device Description"

# Create sample devices for testing
python manage.py manage_devices --action create-sample

# Unassign all devices (emergency reset)
python manage.py manage_devices --action unassign-all
```

### Web Interface
- **Device List**: `/fault_locator/devices/`
- **Device Assignment**: `/fault_locator/assign-device-to-team/`
- **Team Overview**: `/fault_locator/team-overview/`

### Notes
- Only users with device management permissions can assign/unassign devices
- Devices cannot be unassigned if they're being used for active faults
- The system automatically filters out already-assigned devices to prevent conflicts
