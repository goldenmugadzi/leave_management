# Edit Team Template URL Fix Summary

## Problem
The `edit_team.html` template was using `{% url 'simple_assign_fault' %}` without providing a `fault_id` parameter, which caused a `NoReverseMatch` error because the URL pattern `simple_assign_fault` requires a `fault_id` parameter.

## Error Message
```
NoReverseMatch at /fault_locator/teams/1/edit/
Reverse for 'simple_assign_fault' with no arguments not found. 
1 pattern(s) tried: ['fault_locator/simple\\-assign/(?P<fault_id>[0-9]+)/\\Z']
```

## Root Cause
The fault_locator app has two URL patterns for the same view:
1. `path('simple-assign/<int:fault_id>/', views.simple_assign_fault, name='simple_assign_fault')` - requires fault_id
2. `path('simple-assign/', views.simple_assign_fault, name='assign_fault')` - no fault_id required

The template was using the first pattern (`simple_assign_fault`) without providing the required parameter.

## Solution
Fixed the template to use the correct URL pattern:

### Before:
```html
<a href="{% url 'simple_assign_fault' %}?team_id={{ team.id }}">
```

### After:
```html
<a href="{% url 'assign_fault' %}?team_id={{ team.id }}">
```

## Files Modified
1. `templates/fault_locator/edit_team.html` - Fixed the URL reference
2. `templates/fault_locator/advanced_fault_assignment.html` - Fixed similar issue
3. `fault_locator/views.py` - Fixed redirect statements that used incorrect URL pattern

## Testing
- All URL patterns now resolve correctly
- Template renders without NoReverseMatch errors
- Both URL patterns work as intended:
  - `assign_fault` for general fault assignment
  - `simple_assign_fault` for specific fault assignment with fault_id

## Status
✅ **FIXED** - The edit team page should now load without errors.
