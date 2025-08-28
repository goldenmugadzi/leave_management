# Implementation Plan

- [x] 1. Create new data models for dashboard sections
  - Create WeeklyCollections, WeeklyRevenueLost, and DebtorCategory models in executive/general_dashboards/models.py
  - Add proper field validations, constraints, and relationships following existing model patterns
  - Include location-based filtering fields (region, district, depot) consistent with existing models
  - Add audit trail fields (created_at, updated_at, updated_by) for tracking changes
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 6.1_

- [ ] 2. Generate and apply database migrations
  - Create Django migrations for the new models using `python manage.py makemigrations`
  - Apply migrations to update database schema with `python manage.py migrate`
  - Create data migration to populate initial/sample data for testing
  - _Requirements: 6.4, 7.4_

- [ ] 3. Register new models in Django admin (optional backup interface)
  - Add basic admin classes for WeeklyCollections, WeeklyRevenueLost, and DebtorCategory in executive/general_dashboards/admin.py
  - Configure simple admin interfaces for data management backup purposes
  - _Requirements: 7.1, 7.2_

- [x] 4. Update existing API endpoints to include new data
  - Modify `get_regions` and `get_dashboard_data` views in executive/general_dashboards/views.py to include new data sections
  - Update `dashboard_filter` view to handle filtering for WeeklyCollections, WeeklyRevenueLost, and DebtorCategory data
  - Ensure new data follows the same JSON response format as existing sections
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 7.2_

- [x] 5. Update existing save_dashboard_data endpoint for new sections
  - Modify the existing `save_dashboard_data` view in executive/general_dashboards/views.py to handle new data types
  - Add support for saving WeeklyCollections data (ZWL/USD values)
  - Add support for saving WeeklyRevenueLost data (faults/maintenance MWh) with auto-calculation of totals
  - Add support for saving DebtorCategory percentages with auto-recalculation to maintain 100% total
  - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6, 4.7, 4.8, 5.5_

- [x] 6. Update React component state to include new data sections
  - Modify static/custom/dashboard_filter.js to add state properties for weekly_collections, weekly_revenue_lost, and debtors
  - Update the component's initial state structure to match new data requirements
  - Ensure new data sections follow the same state management pattern as existing sections
  - _Requirements: 5.4, 7.3_

- [x] 7. Update React component render method with new sections
  - Modify the render method in static/custom/dashboard_filter.js to replace weekly_sales with weekly_collections
  - Replace weekly_outages section with weekly_revenue_lost section
  - Add new debtors section with category-based percentage display
  - Ensure new sections use the existing renderEditableCell method for inline editing
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 4.2, 4.3, 7.3_

- [x] 8. Extend existing inline editing functionality for new sections
  - Update the existing renderEditableCell method in static/custom/dashboard_filter.js to handle new data types
  - Add validation logic for currency values (ZWL/USD millions) and MWh values
  - Extend the saveChangesToServer method to handle new table types (weekly_collections, weekly_revenue_lost, debtors)
  - _Requirements: 4.4, 4.5, 4.6, 5.5, 7.5_

- [x] 9. Add automatic calculation logic for revenue lost totals
  - Implement JavaScript function to auto-calculate total MWh when faults or maintenance values change
  - Add backend validation to ensure total equals faults + maintenance
  - Prevent manual editing of total field in the interface
  - _Requirements: 2.3, 2.4_

- [x] 10. Implement debtor percentage auto-adjustment logic
  - Create JavaScript function to recalculate other percentages when one category changes
  - Ensure all percentages always sum to 100% after any edit
  - Add visual feedback when percentages are auto-adjusted
  - Add backend validation to enforce 100% total constraint
  - _Requirements: 3.4, 3.6, 4.7_

- [x] 11. Update existing filtering methods for new sections
  - Modify the getFilterData method in static/custom/dashboard_filter.js to handle new data sections
  - Update the onFilterSelectCenters method to refresh weekly_collections, weekly_revenue_lost, and debtors data
  - Ensure the existing location filter controls work seamlessly with new sections
  - _Requirements: 5.1, 5.2, 5.3, 6.2, 6.3_

- [x] 12. Implement data formatting and display logic
  - Add JavaScript functions to format currency values with "M" suffix for millions
  - Add formatting for MWh values with appropriate decimal places
  - Add percentage formatting with "%" symbol for debtor categories
  - Implement default value display ("0.0M", "0.0 MWh", "0.0%") when no data exists
  - _Requirements: 1.3, 1.4, 2.2, 3.5_

- [x] 13. Add error handling and user feedback
  - Implement toast notifications for successful saves and errors
  - Add inline error message display for validation failures
  - Add loading spinners during AJAX operations
  - Implement proper error recovery (revert to previous values on failure)
  - _Requirements: 4.6, 5.6, 7.5_

- [x] 14. Create unit tests for new models
  - Write Django TestCase classes for WeeklyCollections, WeeklyRevenueLost, and DebtorCategory models
  - Test model validation, constraints, and automatic calculations
  - Test location-based filtering and audit trail functionality
  - _Requirements: 7.6_

- [x] 15. Create unit tests for API endpoints
  - Write test cases for all new GET and POST endpoints
  - Test data retrieval with various filter combinations
  - Test inline editing with valid and invalid data
  - Test permission checks and error handling scenarios
  - _Requirements: 7.6_

- [x] 16. Create integration tests for inline editing workflow
  - Write end-to-end tests for complete editing workflow (click, edit, save)
  - Test concurrent editing scenarios and data consistency
  - Test automatic calculations and percentage adjustments
  - Test location filtering integration with all sections
  - _Requirements: 7.6_

- [x] 17. Add CSS styling for new dashboard sections
  - Style new table sections to match existing dashboard design
  - Add hover effects and visual feedback for editable cells
  - Style input fields for inline editing mode
  - Add responsive design for mobile/tablet viewing
  - _Requirements: 7.3_

- [x] 18. Implement data seeding and sample data
  - Create Django management command to populate sample data for testing
  - Add realistic sample data for all three new sections
  - Include data for different locations (regions, districts, depots)
  - _Requirements: 1.4, 2.5, 3.5_

- [x] 19. Add logging and monitoring
  - Implement logging for all data update operations
  - Add performance monitoring for API endpoints
  - Log validation errors and user actions for debugging
  - _Requirements: 7.5_

- [x] 20. Final integration and testing
  - Test complete dashboard functionality with all new sections
  - Verify location filtering works across all sections
  - Test inline editing for all data types
  - Perform cross-browser compatibility testing
  - _Requirements: 1.5, 2.6, 3.7, 4.8, 6.5, 7.6_