## Change Request Update Audit

References:
- Creation baseline (`docs/change_requests_creation_baseline.md`)
- Update flows in `it/change_requests/views.py`

### Shared Issues
1. **Duplicated parsing logic**  
   - Each branch parses/validates dates manually (some missing try/except) instead of reusing the `ChangeRequestService` helpers.  
   - `sanitize_input` is used inconsistently with still referencing `request.POST` later.
2. **Approval resets**  
   - All updates nuke `CRApproval` entries, but creation ensures workflow restarts only when inputs change. We need a guard.

### New Profile Updates (`update_new_profile_request`)
- Only updates `roles_to_action`, `roles_actions`, and a handful of contact fields.  
- Does **not** update creation-required metadata: `originator_company`, `originator_site`, `date_resolution_required`, `application`, job-title fallback, `depot_office`, `training_*` bundle.  
- Uses `request.POST.get('firstname')` (legacy lower-case) but service stores `first_name`.  
- Region/cost center/district lookups don’t align with creation (region forced to creator region).  
- Does not re-run validation before saving; creation enforces required fields.

### Profile Modification / Delegation Updates (`update_change_request`, POST)
- `roles_to_action` overloaded to hold textarea notes. Creation uses it for summarizing role set; temporary delegations rely on `role_to_assign` ManyToMany.  
- Validation requiring assign/remove notes only applies to permanent modifications, but creation allowed blank notes when role IDs are chosen.  
- `delegator`/`delegatee` data cannot change even though creation depends on them; no guard ensuring they stay consistent.  
- `roles_actions` JSON for delegations updated inline without helper; structure can diverge from creation output (e.g., missing `type`, `delegator_id`).  
- `application`, `originator_company/site`, `date_resolution_required` updates partially handled but not shared with new profile path.

### Profile Deactivation Updates (`update_change_request`, POST branch)
- Creation stores timezone-aware datetimes by calling `timezone.make_aware`; update replicates but lacks fallback for invalid timezone or blank strings.  
- No validation ensuring `user` being deactivated matches posted username.  
- Does not reapply `deactivated_by` or ensure `application` stays in sync with `ChangeRequest.application`.  
- Attachments/notes handling exists but duplicates creation logic; no helper.

