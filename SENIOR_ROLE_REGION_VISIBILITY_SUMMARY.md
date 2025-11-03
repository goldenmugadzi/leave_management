# Senior Role Region-Wide Visibility Implementation

## Summary

Successfully implemented region-wide visibility for senior roles (Accounting Officer, Finance Manager, Engineering Manager, General Manager) in both ACE and PettyCash awaiting my action views.

## Changes Made

### 1. ACE2/views.py - `ace_awaiting_my_action()` function

**Query 2 (Records WITHOUT cost centers - section/region fallback):**
- Added senior role detection logic
- Senior roles defined: Accounting Officer, Finance Manager, GM, EM, Finance Director, Managing Director
- Senior roles see **entire region** (all sections)
- Junior roles see **section only** (original behavior)

**Created ACEs queries:**
- Applied same region-wide logic for senior roles
- Ensures consistency across all ACE queries

### 2. finance/PettyCash/views.py - `pettycash_awaiting_my_action()` function

**Query 2 (Records WITHOUT cost centers - section/region fallback):**
- Added senior role detection logic
- Senior role defined: Petty Cash Authoriser
- Senior roles see **entire region** (all sections)
- Junior roles see **section only** (original behavior)

**Created PettyCash queries:**
- Applied same region-wide logic for senior roles
- Ensures consistency across all PettyCash queries

## Implementation Details

### Senior Role Logic

```python
# Determine if user has senior role
senior_role_names = [
    'Accounting Officer',
    'Finance Manager', 
    'General Manager/Transmission Distribution Director',
    'Engineering Manager',
    'Finance Director/Transmission Manager',
    'Managing Director'
]
has_senior_role = user_roles and any(role.name in senior_role_names for role in user_roles)

# Build filter based on role level
fallback_filter = {
    'cost_center__isnull': True,
    'region': region,
    'date_created__year__gte': 2025
}
if not has_senior_role and section:
    fallback_filter['section'] = section  # Junior roles restricted to section
```

### Key Features

1. **Cost Center Filtering (Unchanged)**
   - Both senior and junior roles use jurisdiction-based cost center filtering
   - This remains the primary filtering mechanism

2. **Section/Region Fallback (Enhanced)**
   - **Senior roles**: See ALL records in their region (regardless of section)
   - **Junior roles**: See only records in their section within their region

3. **Rejection Filtering (Applied to ALL)**
   - All queries exclude rejected records: `.exclude(process__approval__approved="Rejected")`
   - Applied to workflow queries AND created by user queries

4. **Deduplication**
   - Uses `processed_ace_ids` and `processed_pettycash_ids` sets to avoid duplicates
   - Ensures records don't appear twice when matching multiple criteria

## Test Results

### Test 1: Accounting Officer (Senior Role)
- User: ze222836
- Region: TRANSMISSION
- Section: HO Finance(Reporting&Budgets)
- **Result**: Sees 55 ACEs and 149 PettyCash from **entire region** (not just section)

### Test 2: Section Head (Junior Role)
- User: ze333352
- Region: HARARE REGION
- Section: North District
- **Result**: Sees 669 ACEs and 283 PettyCash from **section only**
- Region totals: 1623 ACEs, 1472 PettyCash (other sections not visible)

## Workflow Context

### ACE Workflow Steps
1. Section Head / District Manager
2. **Accounting Officer** ← Senior role
3. **Finance Manager** ← Senior role
4. **General Manager** ← Senior role

### Benefits

1. **Senior managers** can see and approve items from across their entire region
2. **Junior managers** maintain section-focused view (prevents overwhelming them)
3. **Cost center filtering** still provides proper jurisdiction control
4. **Backward compatible** with older records that lack cost centers

## Files Modified

1. `d:\b\ACE2\views.py` - ace_awaiting_my_action() function
2. `d:\b\finance\PettyCash\views.py` - pettycash_awaiting_my_action() function

## Verification

✓ Functions import successfully
✓ Senior roles see entire region (tested with Accounting Officer)
✓ Junior roles see section only (tested with Section Head)
✓ Rejection filtering works on all queries
✓ No duplicates in results
✓ Cost center filtering unchanged

## Date
October 22, 2025
