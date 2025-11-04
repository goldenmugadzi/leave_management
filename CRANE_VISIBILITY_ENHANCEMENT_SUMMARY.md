# Crane Visibility Enhancement for Foremen

## Overview

Enhanced the fault locator system to provide better crane visibility for foremen, addressing the need for "more visibility for foremans to seee on availibility of the cranes."

## Implemented Features

### 1. Dashboard Integration

#### Depot Foreperson Dashboard
- **Crane Statistics Section**: Added real-time crane availability stats
  - Total cranes in system
  - Available cranes (ready for assignment)
  - In-service cranes (currently working)
  - Pending requests count
  - Personal requests count
- **Recent Crane Requests Panel**: Shows last 5 crane requests at their depot
- **Quick Access Button**: "Crane Availability" action in secondary menu

#### Senior Foreman Dashboard  
- **System-wide Crane Overview**: Complete visibility across all regions
  - Total cranes across system
  - Available/in-service breakdown
  - Maintenance status tracking
  - Pending and assigned requests
  - Completed jobs today
- **Regional Request Summary**: Crane requests by depot
- **Recent Activity Feed**: All crane requests across depots
- **Management Access**: Full crane availability details

### 2. Dedicated Crane Availability View

#### URL: `/fault_locator/cranes/availability/`

**Features:**
- **Real-time Statistics Cards**
  - Total cranes, availability status
  - Utilization rate calculation
  - Request queue status
- **Available Cranes List**
  - Fleet number and license plate
  - Current mileage
  - Assigned operator
  - Status indicators
- **In-Service Cranes Tracking**
  - Currently working cranes
  - Operator assignments
  - Job locations
- **Pending Requests Table**
  - Request details and descriptions
  - Depot locations
  - Requested dates
  - Requestor information
  - Assignment actions (for senior foremen)
- **Current Assignments Overview**
  - Active crane deployments
  - Job descriptions and locations
  - Progress tracking
- **Regional Overview** (Senior Foreman only)
  - Request distribution by depot
  - Workload balancing view

### 3. Role-Based Access Control

#### Depot Foreperson
- View cranes available for their depot
- See pending requests from their location
- Request new crane assignments
- Track local crane activity

#### Senior Foreman
- System-wide crane visibility
- All regions and depots
- Assign cranes to pending requests
- Regional distribution analysis
- Complete management oversight

## Technical Implementation

### Backend Enhancements
- **Views**: Added `crane_availability()` view in `fault_locator/views.py`
- **Context Data**: Enhanced role context functions with crane statistics
- **Permissions**: Role-based access controls for foreman levels
- **URL Routing**: Added `/cranes/availability/` endpoint

### Frontend Components
- **Dashboard Cards**: Integrated crane stats into existing dashboards
- **Dedicated Template**: `crane_availability.html` with comprehensive views
- **Responsive Design**: Mobile-friendly crane information display
- **Status Indicators**: Color-coded crane and request statuses

### Database Integration
- **Models Used**: `CraneTruck`, `CraneRequest`  
- **Efficient Queries**: Optimized database calls for statistics
- **Real-time Data**: Live status updates and availability tracking

## Usage Guide

### For Depot Forepersons
1. **Dashboard View**: See crane stats directly on role dashboard
2. **Quick Access**: Click "Crane Availability" in secondary actions
3. **Request Tracking**: Monitor your depot's crane requests
4. **Availability Check**: See which cranes are ready for work

### For Senior Foremen
1. **System Overview**: Complete crane fleet visibility on dashboard
2. **Regional Management**: Use availability view for system-wide planning
3. **Request Assignment**: Assign available cranes to pending requests
4. **Performance Monitoring**: Track utilization rates and efficiency

## Benefits

### Improved Visibility
- **Real-time Status**: Immediate crane availability information
- **Request Tracking**: Complete visibility into crane request pipeline
- **Resource Planning**: Better understanding of crane utilization

### Enhanced Efficiency
- **Quick Access**: One-click crane availability checking
- **Informed Decisions**: Data-driven crane allocation
- **Reduced Delays**: Faster identification of available resources

### Better Coordination
- **Regional Overview**: Senior foremen can balance workloads
- **Status Updates**: Real-time crane and request status tracking
- **Communication**: Clear visibility for all foreman levels

## Future Enhancements

### Potential Improvements
- **Mobile Notifications**: Push alerts for crane availability changes
- **Predictive Analytics**: Forecast crane demand patterns
- **GPS Integration**: Real-time crane location tracking
- **Automated Scheduling**: Smart crane assignment algorithms

### Integration Opportunities
- **Vehicle Tracking**: Link with existing vehicle management
- **Work Orders**: Connect with fault locator job assignments
- **Maintenance Scheduling**: Integrate with crane maintenance cycles

## Files Modified

### Views and Logic
- `fault_locator/views.py` - Added crane_availability() function
- `fault_locator/role_views.py` - Enhanced context functions with crane data
- `fault_locator/urls.py` - Added crane availability URL pattern

### Templates
- `templates/fault_locator/crane_availability.html` - Dedicated availability view
- `templates/fault_locator/role_dashboard.html` - Added crane statistics section

### Features Added
- Comprehensive crane visibility for foremen
- Role-based access to appropriate crane information
- Real-time availability statistics and tracking
- Integrated dashboard components for quick access
- Detailed crane request and assignment management

This enhancement significantly improves crane visibility for foremen while maintaining proper role-based access controls and providing the detailed information needed for effective crane resource management.