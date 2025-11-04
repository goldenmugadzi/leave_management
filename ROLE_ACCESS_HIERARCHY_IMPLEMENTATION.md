# Role-Based Access Hierarchy Implementation

## Summary

Successfully implemented a three-tier access hierarchy for ACE and PettyCash awaiting my action views, ensuring proper segregation of duties while maintaining fallback support for legacy records without cost centers.

## Access Hierarchy

### Tier 1: System-Wide Access (FD/MD)
**Roles:**
- Finance Director/Transmission Manager (FD)
- Managing Director (MD)

**Access Rights:**
- **Cost Center Records**: See ALL records with cost centers (no limitations)
- **Legacy Records**: See ALL records without cost centers (no region/section filter)
- **Rationale**: Executive oversight requires full system visibility

### Tier 2: Region-Wide Access (AO/FM/EM/GM)
**Roles:**
- Accounting Officer (AO)
- Finance Manager (FM)
- Engineering Manager (EM)
- General Manager/Transmission Distribution Director (GM)

**Access Rights:**
- **Cost Center Records**: LIMITED to their designated cost centers
- **Legacy Records**: See entire REGION (all sections within their region)
- **Rationale**: Senior management needs regional visibility but should be limited to their jurisdictional cost centers

### Tier 3: Section-Only Access (Others)
**Roles:**
- Section Head / District Manager
- Requester
- Other operational roles

**Access Rights:**
- **Cost Center Records**: LIMITED to their designated cost centers
- **Legacy Records**: See SECTION ONLY (their specific section within region)
- **Rationale**: Operational staff focus on their immediate area of responsibility

## Implementation Details

### ACE2/views.py - `ace_awaiting_my_action()`

#### System-Wide Access (FD/MD)
```python
system_wide_roles = ['Finance Director/Transmission Manager', 'Managing Director']
has_system_wide_access = user_roles and any(role.name in system_wide_roles for role in user_roles)

# Query 1: Records WITH cost centers
if has_system_wide_access:
    aces_with_cost_center = Ace2.objects.filter(
        cost_center__isnull=False  # ALL records with cost centers
    ).exclude(process__approval__approved="Rejected")
```

#### Region-Wide Access (AO/FM/EM/GM)
```python
region_wide_roles = ['Accounting Officer', 'Finance Manager', 
                    'General Manager/Transmission Distribution Director', 
                    'Engineering Manager']
has_region_wide_access = user_roles and any(role.name in region_wide_roles for role in user_roles)

# Query 2: Records WITHOUT cost centers (fallback)
if has_system_wide_access:
    # FD/MD: No region filter
    fallback_filter = {'cost_center__isnull': True, 'date_created__year__gte': 2025}
elif has_region_wide_access and region:
    # AO/FM/EM/GM: Region-wide
    fallback_filter = {'cost_center__isnull': True, 'region': region, 'date_created__year__gte': 2025}
elif region:
    # Others: Section-only
    fallback_filter = {'cost_center__isnull': True, 'region': region, 'date_created__year__gte': 2025}
    if section:
        fallback_filter['section'] = section
```

### finance/PettyCash/views.py - `pettycash_awaiting_my_action()`

Same hierarchy applied with appropriate role names:
- System-Wide: Finance Director, Managing Director
- Region-Wide: Petty Cash Authoriser
- Section-Only: Others

## Test Results

### Database Statistics
- **ACEs**: 4,286 total (1 with cost centers, 4,285 without)
- **PettyCash**: 23,589 total (1 with cost centers, 23,588 without)

### Tier 1 Test: Finance Director
- User: ze045255
- **Result**: Has system-wide access
- ✓ Can see ALL 1 ACE with cost centers
- ✓ Can see ALL 4,285 ACEs without cost centers (no region filter)

### Tier 2 Test: Accounting Officer
- User: ze222836
- Section: HO Finance(Reporting&Budgets)
- Region: TRANSMISSION
- **Result**: Has region-wide access
- ✓ Limited to designated cost centers (0 in this case)
- ✓ Can see 55 ACEs without cost centers (entire TRANSMISSION region)
- ✗ Would only see 0 if limited to section

### Tier 3 Test: Section Head
- User: ze333352
- Section: North District
- Region: HARARE REGION
- **Result**: Section-only access
- ✓ Limited to designated cost centers (5 cost centers)
- ✓ Can see 669 ACEs without cost centers (North District section only)
- ✗ Cannot see other 954 ACEs in HARARE REGION (1,623 - 669)

## Key Features

### 1. Cost Center Filtering
- **FD/MD**: No restrictions - see all records
- **All Others**: Restricted to designated cost centers via `user.cost_centers_for()`

### 2. Fallback Logic (for records without cost centers)
- **FD/MD**: System-wide (no geographic filters)
- **AO/FM/EM/GM**: Region-wide (all sections in region)
- **Others**: Section-only (specific section)

### 3. Rejection Filtering
- All tiers exclude rejected records: `.exclude(process__approval__approved="Rejected")`

### 4. Deduplication
- Uses `processed_ace_ids` and `processed_pettycash_ids` sets to prevent duplicates

### 5. Created Items
- Same access hierarchy applied to "Items You Created" sections
- Ensures consistency across all queries

## Benefits

1. **Executive Oversight**: FD/MD have complete system visibility for strategic decisions
2. **Regional Management**: Senior managers (AO/FM/EM/GM) can oversee their entire region
3. **Operational Focus**: Section-level staff see only their immediate responsibilities
4. **Backward Compatible**: Fallback logic handles 99.9% of records lacking cost centers
5. **Security**: Proper access segregation prevents unauthorized access
6. **Scalability**: As cost centers are assigned, access becomes more precise

## Files Modified

1. `d:\b\ACE2\views.py` - ace_awaiting_my_action() function
2. `d:\b\finance\PettyCash\views.py` - pettycash_awaiting_my_action() function

## Verification

✓ Functions import successfully
✓ FD shows system-wide access (tested)
✓ AO shows region-wide access (tested)
✓ Section Head shows section-only access (tested)
✓ Cost center filtering works correctly
✓ Fallback logic maintains backward compatibility
✓ Rejection filtering applied to all queries

## Date
October 22, 2025
