# Installation Inspections - User Roles Implementation Task

## Overview
Implementation task for adding new user roles and application entry for the Installation Inspections system, supporting the mobile app integration as specified in the Django Server API documentation.

**Date:** September 19, 2025  
**Status:** Pending Implementation  
**Priority:** High  
**Module:** Installation Inspections  

---

## Database Changes Required

### 1. Application Entry
**Table:** `users_application`

```sql
INSERT INTO `users_application` (`fullname`, `id`, `name`) 
VALUES ('Installation Inspections', '25', 'Installation_inspections');
```

**Purpose:** Registers the Installation Inspections application in the system to enable role-based access control.

### 2. User Roles Creation
**Table:** `users_roles`

```sql
INSERT INTO `users_roles` (`app_id_id`, `application`, `description`, `id`, `name`, `role`) 
VALUES 
('25', 'Installation_inspections', 'Inspects Electrical Installations', '135', 'Inspector ', 'inspector'),
('25', 'Installation_inspections', 'Assigns and Review Inspections', '136', 'Foreman', 'foreman'),
('25', 'Installation_inspections', 'Manages User Applications', '137', 'Client Liason', 'client_liason');
```

---

## Role Definitions and Permissions

### Inspector (ID: 135)
**Role Code:** `inspector`  
**Description:** Inspects Electrical Installations

**Permissions:**
- ✅ View assigned applications
- ✅ Accept inspection assignments
- ✅ Create and complete inspections
- ✅ Upload inspection photos and signatures
- ✅ Update inspection status
- ❌ Assign applications to other users
- ❌ Approve final inspection results
- ❌ View all applications system-wide

**API Access:**
- GET `/applications/assigned`
- POST `/applications/:id/accept`
- POST `/applications/:id/complete`
- POST `/inspections`
- POST `/inspections/:id/photos`
- POST `/inspections/:id/signatures`
- PATCH `/inspections/:id/status`

### Foreman (ID: 136)
**Role Code:** `foreman`  
**Description:** Assigns and Review Inspections

**Permissions:**
- ✅ View all applications in district/region
- ✅ Assign applications to inspectors
- ✅ Review completed inspections
- ✅ Approve or reject inspection results
- ✅ Generate inspection reports
- ✅ Monitor inspection progress
- ❌ Perform direct inspections (can if needed)
- ❌ System-wide administration

**API Access:**
- GET `/applications` (with expanded scope)
- POST `/applications/:id/assign`
- PATCH `/applications/:id/status`
- GET `/inspections` (review access)
- POST `/inspections/:id/approve`
- GET `/reports/inspections`

### Client Liaison (ID: 137)
**Role Code:** `client_liason`  
**Description:** Manages User Applications

**Permissions:**
- ✅ View customer applications
- ✅ Update application details
- ✅ Communicate with customers
- ✅ Manage customer information
- ✅ Track application progress
- ✅ Generate customer reports
- ❌ Perform inspections
- ❌ Assign inspections

**API Access:**
- GET `/applications`
- PATCH `/applications/:id` (customer details)
- GET `/customers`
- POST `/customers`
- PATCH `/customers/:id`
- GET `/customers/search`

---

## Implementation Tasks

### Phase 1: Database Setup
- [ ] **Task 1.1:** Execute application registration SQL
  ```sql
  INSERT INTO `users_application` (`fullname`, `id`, `name`) 
  VALUES ('Installation Inspections', '25', 'Installation_inspections');
  ```

- [ ] **Task 1.2:** Execute user roles creation SQL
  ```sql
  INSERT INTO `users_roles` (`app_id_id`, `application`, `description`, `id`, `name`, `role`) 
  VALUES 
  ('25', 'Installation_inspections', 'Inspects Electrical Installations', '135', 'Inspector ', 'inspector'),
  ('25', 'Installation_inspections', 'Assigns and Review Inspections', '136', 'Foreman', 'foreman'),
  ('25', 'Installation_inspections', 'Manages User Applications', '137', 'Client Liason', 'client_liason');
  ```

- [ ] **Task 1.3:** Verify database entries
  ```sql
  SELECT * FROM users_application WHERE id = 25;
  SELECT * FROM users_roles WHERE app_id_id = 25;
  ```

### Phase 2: Django Model Updates
- [ ] **Task 2.1:** Update User model to include new role choices
  ```python
  class UserRole(models.TextChoices):
      INSPECTOR = 'inspector', 'Inspector'
      FOREMAN = 'foreman', 'Foreman'
      CLIENT_LIAISON = 'client_liason', 'Client Liaison'
      # ... existing roles
  ```

- [ ] **Task 2.2:** Create permission groups for each role
  ```python
  # In management command or migration
  inspector_group, _ = Group.objects.get_or_create(name='inspector')
  foreman_group, _ = Group.objects.get_or_create(name='foreman')
  client_liaison_group, _ = Group.objects.get_or_create(name='client_liason')
  ```

- [ ] **Task 2.3:** Define role-specific permissions
  ```python
  # Custom permissions in models
  class Meta:
      permissions = [
          ("can_inspect_installations", "Can inspect installations"),
          ("can_assign_inspections", "Can assign inspections"),
          ("can_manage_applications", "Can manage applications"),
      ]
  ```

### Phase 3: API Authorization Updates
- [ ] **Task 3.1:** Update authentication middleware to recognize new roles
- [ ] **Task 3.2:** Implement role-based permissions in API views
  ```python
  @api_view(['GET'])
  @permission_classes([IsAuthenticated])
  def get_assigned_applications(request):
      if request.user.role == 'inspector':
          # Return only assigned applications
      elif request.user.role == 'foreman':
          # Return applications in district/region
      elif request.user.role == 'client_liason':
          # Return customer-related applications
  ```

- [ ] **Task 3.3:** Add role validation in API endpoints according to spec

### Phase 4: Frontend Integration
- [ ] **Task 4.1:** Update user management interface to support new roles
- [ ] **Task 4.2:** Create role-specific dashboards
- [ ] **Task 4.3:** Implement role-based menu and navigation

### Phase 5: Testing and Validation
- [ ] **Task 5.1:** Create test users for each role
  ```sql
  -- Example for creating test users
  INSERT INTO auth_user (username, role, employee_id, district) 
  VALUES 
  ('test_inspector', 'inspector', 'INS001', 'Harare'),
  ('test_foreman', 'foreman', 'FOR001', 'Harare'),
  ('test_liaison', 'client_liason', 'CLI001', 'Harare');
  ```

- [ ] **Task 5.2:** Test API endpoints with each role
- [ ] **Task 5.3:** Verify permission restrictions work correctly
- [ ] **Task 5.4:** Test mobile app integration with new roles

---

## Data Migration Script

```python
# migration_add_inspection_roles.py
from django.db import migrations

def add_inspection_roles(apps, schema_editor):
    # Add application
    db_alias = schema_editor.connection.alias
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO users_application (fullname, id, name) 
            VALUES ('Installation Inspections', '25', 'Installation_inspections')
            ON DUPLICATE KEY UPDATE 
            fullname = VALUES(fullname), name = VALUES(name)
        """)
        
        cursor.execute("""
            INSERT INTO users_roles (app_id_id, application, description, id, name, role) 
            VALUES 
            ('25', 'Installation_inspections', 'Inspects Electrical Installations', '135', 'Inspector ', 'inspector'),
            ('25', 'Installation_inspections', 'Assigns and Review Inspections', '136', 'Foreman', 'foreman'),
            ('25', 'Installation_inspections', 'Manages User Applications', '137', 'Client Liason', 'client_liason')
            ON DUPLICATE KEY UPDATE 
            description = VALUES(description), name = VALUES(name)
        """)

class Migration(migrations.Migration):
    dependencies = [
        ('your_app', 'previous_migration'),
    ]

    operations = [
        migrations.RunPython(add_inspection_roles),
    ]
```

---

## Role Assignment Process

### For Existing Users
1. **Identify users** who should have these roles
2. **Update user records** with appropriate role assignments
3. **Assign to groups** for permission management
4. **Test access** to ensure proper functionality

### For New Users
1. **Registration process** should include role selection
2. **Automatic group assignment** based on selected role
3. **Default permissions** applied automatically
4. **Welcome workflow** specific to each role

---

## API Integration Points

### Mobile App Authentication Response
```json
{
  "user": {
    "role": "inspector",
    "permissions": {
      "canViewAssignments": true,
      "canAcceptAssignments": true,
      "canCreateInspections": true,
      "canCompleteInspections": true,
      "canViewAllInspections": false,
      "canApproveInspections": false,
      "canAssignInspections": false,
      "canManageCustomers": false
    }
  }
}
```

### Role-Specific Menu Configuration
```json
{
  "inspector": [
    {"label": "My Assignments", "route": "/assignments"},
    {"label": "Active Inspections", "route": "/inspections/active"},
    {"label": "Completed Inspections", "route": "/inspections/completed"}
  ],
  "foreman": [
    {"label": "All Applications", "route": "/applications"},
    {"label": "Assign Inspections", "route": "/assignments/manage"},
    {"label": "Review Inspections", "route": "/inspections/review"}
  ],
  "client_liason": [
    {"label": "Customer Applications", "route": "/customers/applications"},
    {"label": "Manage Customers", "route": "/customers"},
    {"label": "Application Status", "route": "/applications/status"}
  ]
}
```

---

## Success Criteria

- [ ] All three roles successfully created in database
- [ ] Application entry properly registered
- [ ] API endpoints respect role-based permissions
- [ ] Mobile app can authenticate users with new roles
- [ ] Role-specific functionality works as designed
- [ ] No existing functionality is broken

---

## Rollback Plan

If issues arise during implementation:

1. **Database rollback:**
   ```sql
   DELETE FROM users_roles WHERE app_id_id = 25;
   DELETE FROM users_application WHERE id = 25;
   ```

2. **Code rollback:** Revert Django model and API changes
3. **User reassignment:** Update any users assigned these roles
4. **Clear cache:** Clear any cached permission data

---

## Notes and Considerations

1. **Security:** Ensure role permissions don't overlap inappropriately
2. **Performance:** Monitor API performance with new permission checks
3. **Scalability:** Consider district/region-based role assignments
4. **Audit:** Log all role-based actions for compliance
5. **Training:** Prepare documentation for users with new roles

---

**Implementation Owner:** Backend Development Team  
**Review Required:** Security Team, QA Team  
**Estimated Completion:** 1-2 weeks  
**Dependencies:** Django Server API infrastructure