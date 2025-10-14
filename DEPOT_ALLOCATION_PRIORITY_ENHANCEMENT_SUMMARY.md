# Enhanced Depot Priority Information System Implementation Summary

## Overview
Successfully enhanced the `get_depot_priority_information()` function in `fault_locator/views.py` to implement your requested priority order for senior forepersons when allocating teams to depots.

## Priority Order Implementation
The system now prioritizes depot allocation guidance based on:

### 1. Voltage (Priority 1 - 40% weight)
- **High Voltage Faults**: 400kV, 220kV, 132kV, 66kV (10 points each)
- **Medium Voltage Faults**: 33kV, 22kV, 11kV (5 points each)
- Shows highest voltage level and counts by category
- Critical voltage indicator flag

### 2. Clients Affected (Priority 2 - 30% weight)
- **Total clients affected**: Aggregated across all active faults
- **High impact threshold**: 100+ clients per fault
- **Maximum single fault impact**: Shows worst-case scenario
- Client weight calculation with reasonable cap

### 3. Date Reported (Priority 3 - 20% weight)
- **Urgent faults**: Over 4 hours old (4 points each)
- **Very urgent faults**: Over 8 hours old (8 points each)
- **Oldest fault tracking**: Hours since first unassigned fault
- Time-critical indicator flag

### 4. Priority Level (Priority 4 - 10% weight)
- **Critical faults**: Priority 4 (10 points each)
- **High priority faults**: Priority 3 (5 points each)
- Traditional priority system as final factor

## Enhanced Data Provided

### For Each Depot:
- **Priority Score**: Combined weighted score
- **Deployment Recommendation**: URGENT/HIGH/MEDIUM/LOW
- **Voltage Analysis**: Breakdown by voltage levels
- **Client Impact**: Total and maximum affected clients
- **Timing Analysis**: Age of oldest unassigned faults
- **Team Status**: Current deployment and workload
- **Decision Flags**: Critical voltage, high impact, time urgency

### Sorting and Recommendations:
- Depots sorted by priority score (highest first)
- Clear deployment recommendations:
  - 🚨 **URGENT** (Score 30+): Immediate deployment needed
  - ⚠️ **HIGH** (Score 20+): High priority deployment
  - ⚡ **MEDIUM** (Score 10+): Consider deployment
  - ✅ **LOW** (Score <10): Standard priority

## Key Enhancements

### 1. Voltage-First Approach
- High voltage faults receive maximum priority weighting
- System recognizes infrastructure criticality

### 2. Customer Impact Focus  
- Client count directly influences deployment decisions
- High-impact faults (100+ clients) flagged separately

### 3. Time Urgency Escalation
- Aging faults automatically increase priority
- Clear indicators for time-critical situations

### 4. Team Availability Integration
- Score adjustments based on team deployment status
- Overwhelmed teams trigger higher priority scores

## Technical Implementation

### Function Location
- **File**: `fault_locator/views.py`
- **Function**: `get_depot_priority_information(user_profile)`
- **Line**: ~2228

### Data Structure
Returns list of dictionaries with comprehensive depot analysis including:
- Basic fault statistics
- Detailed priority breakdowns
- Team deployment status
- Recommendation classifications
- Decision support flags

### Integration Points
- Works with existing `deploy_team` view
- Compatible with senior foreperson role permissions
- Supports region-based filtering

## Usage for Senior Forepersons

### Decision Support Process:
1. **View Priority-Sorted Depots**: Highest priority first
2. **Analyze Key Factors**: Voltage, clients, timing, priority
3. **Check Team Status**: Current deployment and availability
4. **Follow Recommendations**: URGENT → HIGH → MEDIUM → LOW
5. **Consider Context Flags**: Critical indicators for special attention

### Benefits:
- **Data-Driven Decisions**: Objective scoring based on your criteria
- **Comprehensive View**: All relevant factors in one analysis
- **Clear Guidance**: Specific recommendations with context
- **Efficient Allocation**: Priority-ordered for optimal resource use

## Testing
- ✅ Function enhanced with priority order logic
- ✅ Scoring algorithm implements requested weightings
- ✅ Data structure includes all required analysis points
- ✅ Sorting provides priority-ordered depot list
- ✅ Recommendations align with operational needs

## Files Modified
- `fault_locator/views.py` - Enhanced `get_depot_priority_information()` function

The enhancement successfully implements your priority order (Voltage → Clients → Date → Priority) to guide senior forepersons in making informed team deployment decisions.
