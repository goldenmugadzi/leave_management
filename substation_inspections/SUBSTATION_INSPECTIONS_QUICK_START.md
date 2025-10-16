# Substation Inspections Module - Quick Start Guide

## Prerequisites
- Django application running
- Virtual environment activated
- Database migrations applied
- User accounts created
- Substation inspection roles added to the system

## Quick Setup (15 minutes)

### Step 0: Setup Roles (2 minutes)
First, add the substation inspection roles to your system:

```sql
-- Add application
INSERT INTO `users_application` (`fullname`, `id`, `name`) 
VALUES ('Substation Inspections', '25', 'substation_inspections');

-- Add roles
INSERT INTO `users_roles` (`app_id_id`, `application`, `description`, `id`, `name`, `role`) 
VALUES 
('25', 'substation_inspections', 'System Administrator with full access', '135', 'System Administrator', 'system_admin'),
('25', 'substation_inspections', 'Inspection Supervisor with management access', '136', 'Inspection Supervisor', 'inspection_supervisor'),
('25', 'substation_inspections', 'Field Inspector with limited access', '137', 'Field Inspector', 'field_inspector'),
('25', 'substation_inspections', 'Read-Only User with view access only', '138', 'Read-Only User', 'readonly_user');
```

### Step 1: Access the Module
1. Navigate to the substation inspections module in your browser
2. URL: `http://your-domain/substation-inspections/`
3. You should see the main dashboard
4. Your role will be displayed in the user information section

### Step 2: Create Test Data

#### A. Create Sample Substations (5 minutes)
1. Click **"Add New Substation"**
2. Create 3 test substations:

**Substation 1:**
- Name: `Test Primary Station`
- Type: `Primary Substation`
- Voltage Level: `132kV`
- Location: `Test Location 1`
- District: `Test District`
- Region: `Test Region`
- Transformers: `2`
- Circuit Breakers: `8`
- Switchgear: `6`

**Substation 2:**
- Name: `Test Distribution Station`
- Type: `Distribution Substation`
- Voltage Level: `33kV`
- Location: `Test Location 2`
- District: `Test District`
- Region: `Test Region`
- Transformers: `1`
- Circuit Breakers: `4`
- Switchgear: `3`

**Substation 3:**
- Name: `Test Secondary Station`
- Type: `Secondary Substation`
- Voltage Level: `11kV`
- Location: `Test Location 3`
- District: `Test District`
- Region: `Test Region`
- Transformers: `1`
- Circuit Breakers: `2`
- Switchgear: `2`

#### B. Create Checklist Items (5 minutes)
1. Navigate to **Checklist Items** → **Create New Item**
2. Create 5 sample checklist items:

**Safety Item:**
- Title: `Safety Equipment Check`
- Category: `Safety`
- Severity: `High`
- Description: `Verify all safety equipment is present and functional`
- Reference Standard: `IEEE 141`
- Frequency: `monthly`

**Electrical Item:**
- Title: `Transformer Inspection`
- Category: `Electrical Equipment`
- Severity: `Critical`
- Description: `Check transformer oil levels, temperature, and connections`
- Reference Standard: `IEC 60076`
- Frequency: `monthly`

**Mechanical Item:**
- Title: `Switchgear Operation Test`
- Category: `Mechanical Equipment`
- Severity: `Medium`
- Description: `Test all switchgear operations and mechanisms`
- Reference Standard: `IEC 62271`
- Frequency: `monthly`

**Environmental Item:**
- Title: `Environmental Conditions Check`
- Category: `Environmental`
- Severity: `Low`
- Description: `Check for environmental hazards and conditions`
- Reference Standard: `IEEE 141`
- Frequency: `monthly`

**Security Item:**
- Title: `Security System Check`
- Category: `Security`
- Severity: `Medium`
- Description: `Verify security systems and access controls`
- Reference Standard: `Local Standards`
- Frequency: `monthly`

#### C. Create Inspection Schedules (3 minutes)
1. Navigate to **Schedules** → **Create New Schedule**
2. Create schedules for all 3 substations:

**Schedule 1:**
- Substation: `Test Primary Station`
- Frequency: `Monthly`
- Day of Month: `1`
- Assigned Inspector: `[Select a user]`
- Reminder Days: `3`
- Escalation Days: `2`

**Schedule 2:**
- Substation: `Test Distribution Station`
- Frequency: `Monthly`
- Day of Month: `5`
- Assigned Inspector: `[Select a user]`
- Reminder Days: `3`
- Escalation Days: `2`

**Schedule 3:**
- Substation: `Test Secondary Station`
- Frequency: `Monthly`
- Day of Month: `10`
- Assigned Inspector: `[Select a user]`
- Reminder Days: `3`
- Escalation Days: `2`

### Step 3: Generate Test Inspections (2 minutes)
1. Navigate to **Monitoring Dashboard**
2. Click **"Generate Monthly Inspections"**
3. This will create inspection reports for all scheduled substations

## Testing the Complete Workflow

### Test 1: Basic Inspection Creation
1. Go to **Reports** → **Create New Report**
2. Select `Test Primary Station`
3. Set inspection date to today
4. Fill in weather conditions: `Clear`
5. Set temperature: `25`
6. Set humidity: `60`
7. Add overall condition: `Good condition, no major issues`
8. Save the report

### Test 2: Checklist Inspection
1. Open the inspection report you just created
2. Navigate to the checklist section
3. For each checklist item:
   - Select appropriate response (Pass/Fail/NA)
   - Add observations
   - Mark any defects if found
4. Update status to "In Progress" or "Completed"

### Test 3: Bulk Assignment
1. Go to **Bulk Assignment**
2. Select multiple unassigned inspections
3. Choose an inspector
4. Add notes: `Test bulk assignment`
5. Click **Assign Inspections**

### Test 4: Monitoring Dashboard
1. Navigate to **Monitoring Dashboard**
2. Check the statistics cards
3. Review recent inspections
4. Check upcoming inspections
5. Verify overdue inspections (if any)

### Test 5: Inspector Workload
1. Go to **Inspector Workload**
2. Review each inspector's assignments
3. Check pending and completed counts
4. Verify workload distribution

## Expected Results

After completing the quick start:

### Dashboard Should Show:
- **Total Substations**: 3
- **Pending Inspections**: 3 (or more if you created additional reports)
- **Completed This Month**: 0 (until you complete inspections)
- **Overdue Inspections**: 0 (unless you set past dates)

### Available Features:
- ✅ Substation management
- ✅ Inspection scheduling
- ✅ Report creation and editing
- ✅ Checklist management
- ✅ Bulk assignment
- ✅ Monitoring dashboard
- ✅ Inspector workload tracking

## Quick Test Scenarios

### Scenario A: Normal Inspection Flow
1. Create inspection report
2. Complete all checklist items with "Pass" responses
3. Mark as "Completed"
4. Verify dashboard updates

### Scenario B: Inspection with Issues
1. Create inspection report
2. Mark some checklist items as "Fail"
3. Add defect descriptions
4. Set corrective actions
5. Mark as "Completed"
6. Check compliance status

### Scenario C: Overdue Inspection
1. Create inspection with past date
2. Run overdue notification process
3. Verify status changes to "Overdue"
4. Reassign to different inspector
5. Update to completed

## Troubleshooting Quick Fixes

### Issue: No substations showing
**Fix**: Ensure substations are marked as "Active"

### Issue: Inspections not generating
**Fix**: Check that schedules are active and have assigned inspectors

### Issue: Bulk assignment not working
**Fix**: Ensure selected inspections are in "Scheduled" status

### Issue: Dashboard not updating
**Fix**: Refresh the page or check browser console for errors

## Next Steps

After completing the quick start:

1. **Explore Advanced Features**:
   - Auto-assignment functionality
   - Notification system
   - Report filtering and search
   - Data export capabilities

2. **Customize for Your Needs**:
   - Add more checklist items
   - Create additional substations
   - Set up different inspection frequencies
   - Configure notification settings

3. **Train Users**:
   - Share the full user guide
   - Conduct hands-on training
   - Set up role-based access

4. **Production Setup**:
   - Configure email notifications
   - Set up automated scheduling
   - Implement backup procedures
   - Configure security settings

## Support

If you encounter issues during quick start:
1. Check the main user guide for detailed instructions
2. Verify all prerequisites are met
3. Check Django logs for error messages
4. Contact system administrator for technical support

---

*This quick start guide will get you up and running in 15 minutes. For comprehensive documentation, refer to the full User Guide.*
