# Requirements Document

## Introduction

This feature enhances the existing executive dashboard system to replace current data displays with new business-focused metrics. The enhancement involves updating three key dashboard sections: replacing Sales with Weekly Collections (ZWL/USD), replacing Power Outages with Weekly Revenue Lost (fault/maintenance-based), and implementing a new Debtors section with category-based percentage breakdowns.

## Requirements

### Requirement 1

**User Story:** As an executive user, I want to view weekly collections data in both ZWL and USD currencies (in millions), so that I can track revenue performance across different currency denominations.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL display a "Weekly Collections" section replacing the current "Sales" section
2. WHEN viewing weekly collections THEN the system SHALL show data in two columns: ZWL (millions) and USD (millions)
3. WHEN collections data is displayed THEN the system SHALL format currency values with appropriate million-scale notation (e.g., "5.2M")
4. WHEN no collections data exists for a week THEN the system SHALL display "0.0M" as the default value
5. WHEN collections data is updated THEN the system SHALL reflect changes immediately in the dashboard view

### Requirement 2

**User Story:** As an executive user, I want to view weekly revenue lost data categorized by faults and maintenance (in Megawatt hours), so that I can understand the impact of different operational issues on revenue.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL display a "Weekly Revenue Lost" section replacing the current "Power Outages" section
2. WHEN viewing revenue lost data THEN the system SHALL show three columns: "Revenue lost due to Faults (MWh)", "Revenue lost due to Maintenance (MWh)", and "Total revenue lost (MWh)"
3. WHEN revenue lost data is displayed THEN the system SHALL format values with MWh units
4. WHEN calculating total revenue lost THEN the system SHALL automatically sum fault-based and maintenance-based losses
5. WHEN no revenue lost data exists THEN the system SHALL display "0.0 MWh" as default values
6. WHEN revenue lost data is filtered by location THEN the system SHALL aggregate values appropriately for the selected region/district/depot

### Requirement 3

**User Story:** As an executive user, I want to view debtor information categorized by customer type with percentage breakdowns, so that I can analyze debt distribution across different customer segments.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL display a "Debtors" section with category-based breakdown
2. WHEN viewing debtors data THEN the system SHALL show columns for: ID, Category, and Percentage (%)
3. WHEN displaying debtor categories THEN the system SHALL include: Mining, Domestic, Industry, Commercial, Farming, Government, Parastatal, and Local Authority
4. WHEN calculating percentages THEN the system SHALL ensure all category percentages sum to 100%
5. WHEN no debtor data exists for a category THEN the system SHALL display "0.0%" as the default value
6. WHEN debtor data is updated THEN the system SHALL recalculate percentages automatically to maintain 100% total
7. WHEN filtering by location THEN the system SHALL show location-specific debtor breakdowns

### Requirement 4

**User Story:** As an authorized user, I want to edit dashboard data directly in the interface with inline editing capabilities, so that I can quickly update values without navigating to separate forms.

#### Acceptance Criteria

1. WHEN viewing Weekly Collections data THEN the system SHALL provide inline editing for ZWL and USD values
2. WHEN viewing Weekly Revenue Lost data THEN the system SHALL provide inline editing for fault-based and maintenance-based MWh values
3. WHEN viewing Debtors data THEN the system SHALL provide inline editing for category percentages
4. WHEN clicking on an editable field THEN the system SHALL convert the display to an input field
5. WHEN saving inline edits THEN the system SHALL update the database immediately and reflect changes in real-time
6. WHEN inline editing fails validation THEN the system SHALL display error messages and revert to previous values
7. WHEN editing debtor percentages THEN the system SHALL automatically recalculate other percentages to maintain 100% total
8. WHEN saving edits THEN the system SHALL maintain audit trails with timestamps and user information

### Requirement 5

**User Story:** As an authorized user, I want the new dashboard sections to integrate with the existing React-based frontend filtering system, so that I can filter and edit data consistently across all dashboard sections.

#### Acceptance Criteria

1. WHEN using the existing region/district/depot filters THEN the system SHALL update Weekly Collections data accordingly
2. WHEN using the existing region/district/depot filters THEN the system SHALL update Weekly Revenue Lost data accordingly  
3. WHEN using the existing region/district/depot filters THEN the system SHALL update Debtors data accordingly
4. WHEN the dashboard loads THEN the system SHALL integrate new data sections with the existing React-based dashboard filter component
5. WHEN editing data inline THEN the system SHALL use the existing `save_dashboard_data` API endpoint pattern
6. WHEN data updates occur THEN the system SHALL maintain the existing user permission system for edit access

### Requirement 6

**User Story:** As an executive user, I want the new dashboard sections to maintain the same filtering capabilities as existing sections, so that I can view data by region, district, or depot as needed.

#### Acceptance Criteria

1. WHEN no location filter is applied THEN the system SHALL display aggregated data across all locations
2. WHEN switching between location filters THEN the system SHALL update all three new sections consistently
3. WHEN location filter produces no data THEN the system SHALL display appropriate "No data available" messages
4. WHEN filtering data THEN the system SHALL maintain the same user experience as existing dashboard sections

### Requirement 7

**User Story:** As a developer, I want the new dashboard features to integrate seamlessly with the existing codebase, so that the system maintains consistency and reliability.

#### Acceptance Criteria

1. WHEN implementing new models THEN the system SHALL follow existing Django model patterns and conventions
2. WHEN creating new API endpoints THEN the system SHALL maintain consistency with existing API structure
3. WHEN updating frontend components THEN the system SHALL preserve existing styling and user experience patterns
4. WHEN adding new database migrations THEN the system SHALL ensure backward compatibility
5. WHEN implementing new features THEN the system SHALL include appropriate error handling and logging
6. WHEN testing new functionality THEN the system SHALL maintain existing test coverage standards