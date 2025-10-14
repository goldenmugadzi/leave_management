# Fault Locator Central Roles Integration

This document explains how to integrate fault locator roles with the central user roles system.

## Overview

The fault locator system now supports two role management approaches:

1. **Central Roles System** (Recommended) - Uses `it.users.models.Roles` 
2. **Legacy System** - Uses `fault_locator.models.FaultLocatorRole`

## Benefits of Central Roles System

- ✅ Consistent role management across all applications
- ✅ Better integration with user profiles
- ✅ Easier permission checking
- ✅ Centralized role assignment interface
- ✅ Better reporting and audit trails

## Setup Instructions

### 1. Run the Setup Command

```bash
# Activate your virtual environment
cd d:\b
.\be\Scripts\activate

# Run the setup command
python manage.py setup_fault_locator_roles
```

This command will:
- Create the "fault_locator" application entry
- Create all fault locator roles in the central system
- Migrate existing role assignments

### 2. Available Roles

The system creates these roles:

| Role Code | Display Name | Description |
|-----------|-------------|-------------|
| `senior_foreman` | Senior Foreman | Full administrative access, can manage teams and deployments |
| `depot_foreperson` | Depot Foreperson | Can assign faults at their depot |
| `team_leader` | Team Leader | Can report fault status and manage team work |
| `team_member` | Team Member | Can participate in fault location activities |
| `fault_reporter` | Fault Reporter | Can report new faults |

### 3. Web Interface

Access the role management interface at:
- **Main Management**: `/fault_locator/manage-roles/`
- **Role History**: `/fault_locator/role-history/`
- **Migration Tool**: `/fault_locator/migrate-legacy-roles/`

## Code Usage

### Basic Role Checking

```python
from fault_locator.central_roles import (
    FaultLocatorRoleManager,
    is_senior_foreman,
    is_depot_foreperson,
    is_team_leader
)

# Check if user has specific role
if is_senior_foreman(user_profile):
    # User is a senior foreman
    pass

# Get user's role
user_role = FaultLocatorRoleManager.get_user_role(user_profile)
if user_role == FaultLocatorRoleManager.SENIOR_FOREMAN:
    # User is a senior foreman
    pass
```

### Role Assignment

```python
from fault_locator.central_roles import assign_fault_locator_role

# Assign a role
success = assign_fault_locator_role(
    user_profile, 
    FaultLocatorRoleManager.SENIOR_FOREMAN,
    assigned_by=request.user
)
```

### Permission Checking

```python
from fault_locator.central_roles import can_assign_faults, can_deploy_teams

# Check permissions
if can_assign_faults(user_profile, depot):
    # User can assign faults at this depot
    pass

if can_deploy_teams(user_profile):
    # User can deploy teams
    pass
```

### Get Users by Role

```python
# Get all senior foremen
senior_foremen = FaultLocatorRoleManager.get_users_with_role(
    FaultLocatorRoleManager.SENIOR_FOREMAN
)

# Get all users with any fault locator role
users_with_roles = UserProfile.objects.filter(
    roles__application='fault_locator'
).distinct()
```

## Migration from Legacy System

### Automatic Migration

The setup command automatically migrates existing `FaultLocatorRole` assignments.

### Manual Migration

```python
from fault_locator.central_roles import migrate_legacy_roles

migrated, errors = migrate_legacy_roles()
print(f"Migrated: {migrated}")
if errors:
    for error in errors:
        print(f"Error: {error}")
```

### Web Interface Migration

Visit `/fault_locator/migrate-legacy-roles/` to use the web interface.

## Integration with Views

### View Decorator Example

```python
from django.contrib.auth.decorators import login_required
from fault_locator.central_roles import is_senior_foreman

@login_required
def senior_foreman_only_view(request):
    user_profile = UserProfile.objects.get(id=request.user.id)
    
    if not is_senior_foreman(user_profile):
        messages.error(request, "Access denied")
        return redirect('fault_locator_dashboard')
    
    # View logic here
    pass
```

### Template Usage

```html
<!-- In your templates -->
{% load static %}

<script>
// Check user role in JavaScript
var userRole = "{{ user_profile.get_user_role_for_application:'fault_locator' }}";
if (userRole === "senior_foreman") {
    // Show senior foreman options
}
</script>
```

## URL Configuration

Add to your `urls.py`:

```python
from fault_locator import central_role_views

urlpatterns = [
    # ... existing URLs
    
    # Central Role Management
    path('manage-roles/', central_role_views.manage_fault_locator_roles, name='manage_fault_locator_roles'),
    path('assign-role-ajax/', central_role_views.assign_fault_locator_role_ajax, name='assign_fault_locator_role_ajax'),
    path('remove-role-ajax/', central_role_views.remove_fault_locator_role_ajax, name='remove_fault_locator_role_ajax'),
    path('role-history/', central_role_views.role_assignment_history, name='role_assignment_history'),
    path('migrate-legacy-roles/', central_role_views.migrate_legacy_roles_view, name='migrate_legacy_roles'),
]
```

## Database Schema

### Central Roles Tables

The system uses these existing tables:
- `it_users_application` - Applications
- `it_users_roles` - Role definitions
- `it_users_userprofile_roles` - User-role assignments

### Legacy Tables

The legacy `fault_locator_faultlocatorrole` table is preserved for history but marked inactive.

## Troubleshooting

### Common Issues

1. **"Application not found" error**
   ```bash
   python manage.py setup_fault_locator_roles
   ```

2. **Migration not working**
   - Check that legacy roles exist
   - Verify user profiles are valid
   - Check database permissions

3. **Permission errors**
   - Ensure user has active role assignment
   - Check role spelling (case-sensitive)
   - Verify user profile exists

### Debug Commands

```python
# Check system status
python fault_locator/setup_central_roles.py

# Check user's role
user = UserProfile.objects.get(username='your_username')
role = FaultLocatorRoleManager.get_user_role(user)
print(f"User role: {role}")

# Check available roles
roles = FaultLocatorRoleManager.get_available_roles()
for role in roles:
    print(f"{role.role}: {role.name}")
```

## Best Practices

1. **Always use the central system** for new development
2. **Migrate legacy roles** as soon as possible
3. **Use the role constants** instead of hardcoded strings
4. **Check permissions in views** before allowing actions
5. **Use the web interface** for role management
6. **Test role assignments** thoroughly

## API Reference

### FaultLocatorRoleManager

- `get_user_role(user_profile)` - Get user's role code
- `get_user_role_display(user_profile)` - Get user's role display name
- `assign_role(user_profile, role_code, assigned_by=None)` - Assign role
- `remove_role(user_profile)` - Remove role
- `has_role(user_profile, role_code)` - Check specific role
- `has_any_role(user_profile)` - Check if user has any role
- `get_users_with_role(role_code)` - Get users with specific role
- `get_available_roles()` - Get all available roles

### Permission Functions

- `is_senior_foreman(user_profile)` - Check senior foreman
- `is_depot_foreperson(user_profile, depot_code=None)` - Check depot foreperson
- `is_team_leader(user_profile)` - Check team leader
- `is_team_member(user_profile)` - Check team member
- `can_assign_faults(user_profile, depot=None)` - Check fault assignment permission
- `can_deploy_teams(user_profile)` - Check team deployment permission
- `can_manage_devices(user_profile)` - Check device management permission

## Support

For issues or questions:
1. Check this README
2. Check the Django admin for role assignments
3. Use the debug commands provided
4. Review the setup script output
