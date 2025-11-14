## Legacy Change Request Form – Section Mapping

_Source reference: “INFORMATION TECHNOLOGY DIVISION – USER PROFILE MAINTENANCE (PROF 112011 REL 02)” PDF._

### Global Sections
| Legacy Section | Description | Fields | Applies To |
| --- | --- | --- | --- |
| Section A – Change Request Originator | Base request metadata | Company, Site, Originator name, Designation, Signature, Date Raised, Date Resolution Required | All CR types |
| Section F – Change Authorisation | Approver sign-off | Authorised by, Designation, Signature, Date | All CR types |
| Section G – Implementation | Implementation record | Change Made By, Designation, Signature, Date of Change | All CR types |

### Type-Specific Sections

#### Section C – Creation of New Profile
- **Fields:** Application/Module, Sub Module, EC Number, First Name, Last Name, Username, Job Title, Company, Region/Power Station/Division, District, Depot/Office, Reason for Creating New Profile, Date of Training, Training Evidence (link/attachment).
- **Applicable CR Types:** New Profile only.

#### Section D – Profile Modification (Assignment and/or Removal of Roles)
- **Existing User Information:** Current User ID, EC Number, Surname, First Name.
- **Change Instructions:** New Roles to be Assigned, Reasons for Assigning New Roles, Current Roles to be Removed, Reason for Removing Current Roles, Correspondence/Instruction attachment/link.
- **Applicable CR Types:** Profile Modification, Temporary Role Delegation (shares section but with delegation metadata).

#### Section D (Delegation Variant) – Temporary Role Delegation
- **Delegator Metadata:** Delegator Name/Username, Delegator Region/Designation (inferred from role assignments).
- **Delegatee Metadata:** Delegatee Name/Username (same as user being modified).
- **Delegation Window:** Start Date, End Date (max 90 days), Delegation Reason/Notes, Roles to Delegate (list).
- **Applicable CR Types:** Temporary Role Delegation only.

#### Section E – Deactivation of Profile
- **Fields:** Effective Start Date, Reactivation Date (optional), Reason for Deactivation, Correspondence/Instruction details.
- **Applicable CR Types:** Profile Deactivation only.

### Implications for New UI
1. **Section Ordering:** View-only pages should mirror the legacy order: Section A → type-specific section (C/D/E) → consolidated roles/training data → Section F → Section G.
2. **Conditional Visibility:** Only the sections relevant to the CR type should render; e.g., Section C hidden for modification/deactivation.
3. **Label Parity:** Field labels must match legacy wording (“Date Resolution Required,” “Reason for Creating New Profile,” etc.) to avoid confusion during audits.
4. **Read-only Cards:** Edit forms must include read-only cards for each section so approvers can scan the same data even when inputs are editable.

