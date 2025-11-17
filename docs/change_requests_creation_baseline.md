## Change Request Creation Baseline

Source of truth: `it/change_requests/services/cr_service.py`

### Common ChangeRequest fields
- `cr_id` auto generated as `CR-YYYYMMDDhhmmss`
- `application` from `data['for_application']`
- `change_type` literal per handler
- `change_reason`, `change_description`
- `originator_company`, `originator_site`
- `date_resolution_required` parsed via `datetime.strptime(..., "%Y-%m-%d")`
- `creator_designation` from `request.user.designation`
- `created_by` is request user profile
- `region` set to requestor region (new profile uses user region; others use request.user.region)
- `cost_center` set to requestor cost center
- `created_at` `timezone.now()`

### New Profile (`create_new_profile_cr`)
- New `NewProfile` built before CR
  - Looks up FK objects by id strings passed in POST (`cost_center`, `designation`, `section`, `district`)
  - Region forced to requestor region
  - Date parsing
    - `date_resolution_required` optional
    - `np_training_date` or `training_date` parsed as `YYYY-MM-DD`
  - Job title fallback to designation description if blank
  - Company taken from `np_company`/`company` (string or id resolved earlier)
  - Optional metadata: depot office, sub-module, training confirmation link, `roles_to_action`
- ChangeRequest links `new_profile` and stores same change meta.

### Profile Modification (`create_profile_modification_cr`)
- Requires both `delegator` and `delegatee` usernames (lookup `UserProfile`)
- Creates `ProfileChange` first:
  - `user` = delegatee
  - `application` from form
  - `roles_to_action` raw text; actual assigned roles determined later
  - `change_date` `timezone.now()`
  - `changed_by` = request user (delegator)
  - `current_user_id` uses `mod_current_user_id`/`mod_ec_number`
  - `ec_number` from `mod_ec_number`/`ec_number`
  - `reason_assign` & `reason_remove`, `correspondence_link`
  - `status` preset `PENDING`
- ChangeRequest:
  - `change_type` becomes `Temporary Role Delegation` if `change_type == 'TEMPORARY'` else `Profile Modification`
  - shares standard metadata with requestor region/cost center

### Profile Deactivation (`create_profile_deactivation_cr`)
- Requires `username`/`user_profile` to deactivate (lookup `UserProfile`)
- Parses:
  - `date_resolution_required` (YYYY-MM-DD)
  - `deactivation_effective_start` and `deactivation_reactivation_date` (datetime-local)
  - converts datetimes to aware objects via `timezone.make_aware`
- Creates `ProfileDeactivation`:
  - `user` target user
  - `application`, `deactivation_date` (effective start or now)
  - `effective_start_date`, `reactivation_date`
  - `deactivation_reason`, `correspondence_link`
  - `deactivated_by` request user
- ChangeRequest links `profile_deactivation` with standard metadata.

### Key Derived/Data Integrity Rules
- All dates validated before saving (ValueError if format mismatch)
- Job title defaults to designation description if blank for new profiles
- Delegation `change_type` naming depends on temp/permanent input
- Profile modification uses ManyToMany `role_to_assign` for actual delegated roles; stored text is fallback only
- Deactivation datetimes stored as timezone-aware

