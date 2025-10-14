# Depot Foreperson Team Interaction Restrictions - Implementation Summary

## Overview
Implemented restrictions so that depot forepersons can only interact with teams that are deployed to their specific depot, while senior foremen retain full access to all teams.

## Changes Made

### 1. Team Overview View (`team_overview` function)
**File**: `d:\b\fault_locator\views.py`

**Changes**:
- Added `user_depot` retrieval using `get_user_depot(user_profile)`
- Added `can_interact_with_team` logic that checks:
  - Senior foremen can interact with any team
  - Depot forepersons can only interact with teams deployed to their depot
- Updated action buttons to use `can_interact_with_team` instead of just `is_senior_foreman`
- Added `can_interact_with_team` to the team data context for template use
- Added `is_depot_foreperson` to the template context

### 2. Recall Team Function (`recall_team`)
**File**: `d:\b\fault_locator\views.py`

**Changes**:
- Updated permission check to allow depot forepersons to recall teams from their depot
- Added logic to check if the team is deployed to the user's depot before allowing recall
- Maintained existing restriction that only senior foremen can deploy teams

### 3. Team Overview Template
**File**: `d:\b\templates\fault_locator\team_overview.html`

**Changes**:
- Updated "Recall from Depot" button condition from `is_senior_foreman` to `item.can_interact_with_team`
- This allows depot forepersons to see and use the recall button for teams at their depot

## Permission Logic

### Senior Foremen
- ✅ Can interact with any team (deployed or not)
- ✅ Can deploy teams to any depot
- ✅ Can recall teams from any depot
- ✅ Can edit any team

### Depot Forepersons
- ✅ Can only interact with teams deployed to their depot
- ❌ Cannot interact with teams at other depots
- ❌ Cannot interact with undeployed teams
- ❌ Cannot deploy teams (only senior foremen can do this)
- ✅ Can recall teams from their depot
- ✅ Can edit teams deployed to their depot

### Implementation Details

#### Team Interaction Check:
```python
can_interact_with_team = False

if is_senior_foreman(user_profile):
    can_interact_with_team = True
elif is_depot_foreperson(user_profile, user_depot):
    # Depot foreperson can only interact with teams deployed to their depot
    can_interact_with_team = (team.current_depot == user_depot)
```

#### Recall Permission Check:
```python
if is_senior_foreman(user_profile) or can_manage_devices(user_profile):
    can_recall_team = True
elif is_depot_foreperson(user_profile, user_depot):
    # Depot foreperson can only recall teams from their depot
    can_recall_team = (team.current_depot == user_depot)
```

## Functions That Remain Unchanged

### Still Restricted to Senior Foremen Only:
- `deploy_team()` - Only senior foremen can deploy teams
- `assign_team_to_depot()` - Only senior foremen can assign teams to depots
- Device management functions - Only senior foremen can manage devices

### Already Had Proper Restrictions:
- `simple_assign_fault()` - Depot forepersons can only assign faults at their depot
- Team creation functions - Properly restricted

## Testing

Created comprehensive test suite that verifies:
- ✅ Senior foremen can interact with any team
- ✅ Depot forepersons can interact with teams at their depot
- ✅ Depot forepersons cannot interact with teams at other depots
- ✅ Depot forepersons cannot interact with undeployed teams
- ✅ Different depot forepersons cannot interact with each other's teams

## User Experience Impact

### For Depot Forepersons:
- Will only see teams deployed to their depot in the team overview
- Can recall teams from their depot using the "Recall from Depot" button
- Can edit teams deployed to their depot
- Cannot deploy new teams (must request senior foreman)

### For Senior Foremen:
- No change in functionality - retain full access to all teams
- Can still deploy, recall, and manage any team system-wide

## Security Benefits

1. **Depot Isolation**: Depot forepersons can only affect operations at their assigned depot
2. **Clear Hierarchy**: Senior foremen maintain strategic oversight while depot forepersons handle local operations
3. **Controlled Access**: Prevents accidental or unauthorized team recalls from other depots
4. **Audit Trail**: All team interactions are logged with proper user context

## Future Enhancements

Potential improvements that could be added:
- Emergency override capability for depot forepersons
- Cross-depot team transfer requests
- Temporary permission escalation system
- Team sharing between neighboring depots
