## Change Request View Audit

### Parallel View Paths
- Legacy: `view_profile_request` + `view_new_profile_request`/`view_profile_modification_request`/`view_profile_deactivation_request`.
- Refactored: `view_change_request_unified` + `CRTypeHandler` + `ContextBuilder`.
- Both sets render `templates/change_requests/view_change_request.html`, but the legacy path builds context manually, duplicating logic from handlers and risking drift from creation baseline.

### Gaps vs Creation Data
1. **New Profile**
   - Legacy view constructs `new_user` dict by fetching related lookups individually. Creation already saves the FK objects, so this duplication causes N queries and may omit new fields (e.g., `training_confirmation_notes`, `roles_to_action` updates).
   - `info_items` and info panel rely on `originator_*` values, but only unified view populates `context['info_items']`; legacy branch duplicates snippet and sometimes omits it.

2. **Profile Modification / Delegation**
   - `view_profile_modification_request` rebuilds delegation metadata with `parse_delegation_data`, while handlers already centralize this. Divergences (e.g., `delegation_info.is_delegation`, assigned roles) lead to inconsistent displays between unified vs legacy routes.
   - Template expects `cr.delegation_info.assigned_roles`, `cr.cr_context`, etc.—fields always supplied by handlers but only sometimes by legacy context.
   - Roles-to-action string forcibly rebuilt from `role_to_assign`, while creation sets `roles_to_action` meaningfully for permanent modifications.

3. **Profile Deactivation**
   - Legacy branch passes raw `ProfileDeactivation` object under `cr['user']` whereas handler normalizes dictionaries similar to creation baseline (strings vs model instances). Templates rely on `display_field` expecting friendly strings.

4. **Template Action Targets**
   - `view_change_request.html` form posts to `/change_requests/approve_cr`, but unified backend introduced `approve_change_request_unified`. Without aligning URLs, new handler context still submits to legacy endpoint.

### Required Alignment
- Favor `view_change_request_unified` and remove/redirect legacy functions to ensure all display data flows through `CRTypeHandler`/`ContextBuilder`.
- Ensure templates read data solely from the standardized `cr` context plus `info_items` to prevent missing fields when new metadata is added during creation.

