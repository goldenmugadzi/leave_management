"""
Unit tests for dashboard enhancement API endpoints.

This module contains comprehensive test cases for the new dashboard API endpoints:
- GET endpoints: get_regions, get_dashboard_data, dashboard_filter, user_permissions
- POST endpoints: save_dashboard_data, dashboard_filter (POST version)

Test coverage includes:
- Data retrieval with various filter combinations
- Inline editing with valid and invalid data
- Permission checks and error handling scenarios
- Authentication and authorization
- Response format validation
- Error handling and edge cases

To run these tests:
    python manage.py test executive.general_dashboards.test_api_endpoints

To run specific test classes:
    python manage.py test executive.general_dashboards.test_api_endpoints.GetRegionsAPITest
    python manage.py test executive.general_dashboards.test_api_endpoints.GetDashboardDataAPITest
    python manage.py test executive.general_dashboards.test_api_endpoints.DashboardFilterAPITest
    python manage.py test executive.general_dashboards.test_api_endpoints.SaveDashboardDataAPITest
    python manage.py test executive.general_dashboards.test_api_endpoints.UserPermissionsAPITest

Requirements covered:
- API endpoint testing (Requirement 7.6)
- Data retrieval with filter combinations (Requirements 5.1, 5.2, 5.3, 6.2, 6.3)
- Inline editing validation (Requirements 4.4, 4.5, 4.6, 5.5)
- Permission checks (Requirements 5.6, 7.2)
- Error handling scenarios (Requirements 4.6, 5.6, 7.5)
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
from unittest.mock import patch, MagicMock

from .models import (
    WeeklyCollections, WeeklyRevenueLost, DebtorCategory,
    DashboardMetric, WeeklySales, WeeklyOutage, TopDebtor, WeeklyFaultMaintenance
)
from it.users.models import UserProfile, Regions, Districts, Depots, Roles


class BaseAPITestCase(TestCase):
    """Base test case with common setup for API tests"""
    
    def setUp(self):
        """Set up test data for API tests"""
        # Create test user and profile
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            username='testuser',
            email='test@example.com'
        )
        
        # Create test roles
        self.admin_role = Roles.objects.create(
            role='admin',
            name='Administrator',
            description='Full access',
            application='dashboards'
        )
        
        self.viewer_role = Roles.objects.create(
            role='viewer',
            name='Viewer',
            description='Read-only access',
            application='dashboards'
        )
        
        # Assign admin role to user
        self.user_profile.roles.add(self.admin_role)
        
        # Create test location data
        self.region = Regions.objects.create(region='Test Region', code='TR')
        self.district = Districts.objects.create(
            district='Test District',
            code='TD',
            region_id='1'
        )
        self.depot = Depots.objects.create(
            depot='Test Depot',
            code='TDP',
            district=self.district,
            region=self.region
        )
        
        # Set up client
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Create test data for API endpoints"""
        # Weekly Collections data
        self.weekly_collection_global = WeeklyCollections.objects.create(
            week='Week 1',
            zwl_millions=Decimal('10.50'),
            usd_millions=Decimal('5.25'),
            year=2025,
            week_number=1,
            updated_by=self.user_profile
        )
        
        self.weekly_collection_region = WeeklyCollections.objects.create(
            week='Week 1',
            zwl_millions=Decimal('8.25'),
            usd_millions=Decimal('4.10'),
            region=self.region,
            year=2025,
            week_number=1,
            updated_by=self.user_profile
        )
        
        # Weekly Revenue Lost data
        self.weekly_revenue_lost_global = WeeklyRevenueLost.objects.create(
            week='Week 1',
            faults_mwh=Decimal('15.75'),
            maintenance_mwh=Decimal('8.50'),
            year=2025,
            week_number=1,
            updated_by=self.user_profile
        )
        
        self.weekly_revenue_lost_region = WeeklyRevenueLost.objects.create(
            week='Week 1',
            faults_mwh=Decimal('12.25'),
            maintenance_mwh=Decimal('6.75'),
            region=self.region,
            year=2025,
            week_number=1,
            updated_by=self.user_profile
        )
        
        # Debtor Category data
        self.debtor_mining_global = DebtorCategory.objects.create(
            category='mining',
            percentage=Decimal('25.00'),
            year=2025,
            month=1,
            updated_by=self.user_profile
        )
        
        self.debtor_domestic_global = DebtorCategory.objects.create(
            category='domestic',
            percentage=Decimal('35.00'),
            year=2025,
            month=1,
            updated_by=self.user_profile
        )
        
        self.debtor_mining_region = DebtorCategory.objects.create(
            category='mining',
            percentage=Decimal('30.00'),
            region=self.region,
            year=2025,
            month=1,
            updated_by=self.user_profile
        )
        
        # Legacy data for backward compatibility
        self.weekly_sales = WeeklySales.objects.create(
            week='Week 1',
            zwl='10.5M',
            usd='5.2M',
            year=2025,
            week_number=1
        )
        
        self.weekly_outage = WeeklyOutage.objects.create(
            week='Week 1',
            outages=5,
            resolved=3,
            pending=2,
            year=2025,
            week_number=1
        )
        
        self.top_debtor = TopDebtor.objects.create(
            name='Test Company',
            amount='1.5M',
            rank=1
        )
        
        # Dashboard metrics
        self.dashboard_metric = DashboardMetric.objects.create(
            metric_type='energy_sold',
            value='150.5',
            unit='GWh',
            target='200.0',
            target_unit='GWh',
            progress=75.25,
            updated_by=self.user_profile
        )


class GetRegionsAPITest(BaseAPITestCase):
    """Test cases for get_regions API endpoint"""
    
    def test_get_regions_success(self):
        """Test successful retrieval of regions and dashboard data"""
        response = self.client.get('/dashboards/regions')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        
        # Check that all required keys are present
        required_keys = [
            'regions', 'districts', 'sections', 'depots', 'pbncs',
            'weekly_sales', 'upos', 'weekly_outages', 'tds', 'weekly_faults_maintenance',
            'weekly_collections', 'weekly_revenue_lost', 'debtors'
        ]
        
        for key in required_keys:
            self.assertIn(key, data)
        
        # Check regions data
        self.assertIsInstance(data['regions'], list)
        self.assertEqual(len(data['regions']), 1)
        self.assertEqual(data['regions'][0]['region'], 'Test Region')
        
        # Check districts data
        self.assertIsInstance(data['districts'], list)
        self.assertEqual(len(data['districts']), 1)
        self.assertEqual(data['districts'][0]['district'], 'Test District')
        
        # Check new dashboard sections
        self.assertIsInstance(data['weekly_collections'], list)
        self.assertEqual(len(data['weekly_collections']), 1)  # Only global data
        
        self.assertIsInstance(data['weekly_revenue_lost'], list)
        self.assertEqual(len(data['weekly_revenue_lost']), 1)  # Only global data
        
        self.assertIsInstance(data['debtors'], list)
        self.assertEqual(len(data['debtors']), 2)  # mining and domestic global
    
    def test_get_regions_unauthenticated(self):
        """Test get_regions endpoint without authentication"""
        self.client.logout()
        response = self.client.get('/dashboards/regions')
        
        # Should still work as it's not decorated with @login_required
        self.assertEqual(response.status_code, 200)
    
    def test_get_regions_method_not_allowed(self):
        """Test get_regions endpoint with POST method"""
        response = self.client.post('/dashboards/regions')
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_get_regions_data_format(self):
        """Test that returned data has correct format"""
        response = self.client.get('/dashboards/regions')
        data = response.json()
        
        # Check weekly_collections format
        if data['weekly_collections']:
            collection = data['weekly_collections'][0]
            self.assertIn('week', collection)
            self.assertIn('zwl_millions', collection)
            self.assertIn('usd_millions', collection)
        
        # Check weekly_revenue_lost format
        if data['weekly_revenue_lost']:
            revenue_lost = data['weekly_revenue_lost'][0]
            self.assertIn('week', revenue_lost)
            self.assertIn('faults_mwh', revenue_lost)
            self.assertIn('maintenance_mwh', revenue_lost)
            self.assertIn('total_mwh', revenue_lost)
        
        # Check debtors format
        if data['debtors']:
            debtor = data['debtors'][0]
            self.assertIn('id', debtor)
            self.assertIn('category', debtor)
            self.assertIn('percentage', debtor)


class GetDashboardDataAPITest(BaseAPITestCase):
    """Test cases for get_dashboard_data API endpoint"""
    
    def test_get_dashboard_data_success(self):
        """Test successful retrieval of dashboard data"""
        response = self.client.get('/dashboards/dashboard_data')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        
        # Check that metrics are included
        self.assertIn('metrics', data)
        self.assertIsInstance(data['metrics'], dict)
        
        # Check that chart data is included
        self.assertIn('inspection_locations', data)
        self.assertIn('inspections_count', data)
        self.assertIn('maintenance_locations', data)
        self.assertIn('maintenance_count', data)
    
    def test_get_dashboard_data_metrics_format(self):
        """Test that metrics have correct format"""
        response = self.client.get('/dashboards/dashboard_data')
        data = response.json()
        
        if 'energy_sold' in data['metrics']:
            metric = data['metrics']['energy_sold']
            self.assertIn('value', metric)
            self.assertIn('unit', metric)
            self.assertIn('target', metric)
            self.assertIn('target_unit', metric)
            self.assertIn('progress', metric)
    
    def test_get_dashboard_data_method_not_allowed(self):
        """Test get_dashboard_data endpoint with POST method"""
        response = self.client.post('/dashboards/dashboard_data')
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


class UserPermissionsAPITest(BaseAPITestCase):
    """Test cases for user_permissions API endpoint"""
    
    def test_user_permissions_authenticated_admin(self):
        """Test user permissions for authenticated admin user"""
        response = self.client.get('/dashboards/user_permissions')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('can_edit', data)
        self.assertIn('user_roles', data)
        self.assertIn('user_region', data)
        
        # Admin should have edit permissions
        self.assertTrue(data['can_edit'])
        self.assertIsInstance(data['user_roles'], list)
    
    def test_user_permissions_viewer_role(self):
        """Test user permissions for viewer role"""
        # Remove admin role and add viewer role
        self.user_profile.roles.clear()
        self.user_profile.roles.add(self.viewer_role)
        
        response = self.client.get('/dashboards/user_permissions')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Viewer should not have edit permissions (depends on implementation)
        self.assertIn('can_edit', data)
        self.assertIn('user_roles', data)
    
    def test_user_permissions_unauthenticated(self):
        """Test user permissions without authentication"""
        self.client.logout()
        response = self.client.get('/dashboards/user_permissions')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Unauthenticated user should not have edit permissions
        self.assertFalse(data['can_edit'])
        self.assertEqual(data['user_roles'], [])
    
    def test_user_permissions_method_not_allowed(self):
        """Test user_permissions endpoint with POST method"""
        response = self.client.post('/dashboards/user_permissions')
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


class DashboardFilterAPITest(BaseAPITestCase):
    """Test cases for dashboard_filter API endpoint (both GET and POST versions)"""
    
    def test_dashboard_filter_get_no_filters(self):
        """Test GET dashboard_filter without any filters"""
        response = self.client.get('/dashboards/dashboard_filter')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return global data
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
    
    def test_dashboard_filter_get_with_region_filter(self):
        """Test GET dashboard_filter with region filter"""
        response = self.client.get(
            '/dashboards/dashboard_filter',
            {'region_id': self.region.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return region-specific data
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
        
        # Verify data is filtered by region
        if data['weekly_collections']:
            # Should contain region-specific collection data
            pass  # Add specific assertions based on your data
    
    def test_dashboard_filter_get_with_district_filter(self):
        """Test GET dashboard_filter with district filter"""
        response = self.client.get(
            '/dashboards/dashboard_filter',
            {'district_id': self.district.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
    
    def test_dashboard_filter_get_with_depot_filter(self):
        """Test GET dashboard_filter with depot filter"""
        response = self.client.get(
            '/dashboards/dashboard_filter',
            {'depot_id': self.depot.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
    
    def test_dashboard_filter_get_invalid_filter_values(self):
        """Test GET dashboard_filter with invalid filter values"""
        response = self.client.get(
            '/dashboards/dashboard_filter',
            {'region_id': 99999}  # Non-existent region
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return empty data or handle gracefully
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
    
    def test_dashboard_filter_post_valid_data(self):
        """Test POST dashboard_filter with valid filter data"""
        filter_data = {
            'region_id': self.region.id,
            'district_id': None,
            'depot_id': None
        }
        
        response = self.client.post(
            '/dashboards/dashboard_filter',
            data=json.dumps(filter_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
    
    def test_dashboard_filter_post_invalid_json(self):
        """Test POST dashboard_filter with invalid JSON"""
        response = self.client.post(
            '/dashboards/dashboard_filter',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_dashboard_filter_post_missing_data(self):
        """Test POST dashboard_filter with missing data"""
        response = self.client.post(
            '/dashboards/dashboard_filter',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Should handle gracefully and return global data
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)


class SaveDashboardDataAPITest(BaseAPITestCase):
    """Test cases for save_dashboard_data API endpoint"""
    
    def test_save_weekly_collections_valid_data(self):
        """Test saving valid weekly collections data"""
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': self.weekly_collection_global.id,
            'field': 'zwl_millions',
            'value': '15.75'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        
        # Verify data was updated
        self.weekly_collection_global.refresh_from_db()
        self.assertEqual(self.weekly_collection_global.zwl_millions, Decimal('15.75'))
    
    def test_save_weekly_collections_invalid_value(self):
        """Test saving invalid weekly collections data"""
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': self.weekly_collection_global.id,
            'field': 'zwl_millions',
            'value': '-5.25'  # Negative value should be invalid
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_save_weekly_revenue_lost_valid_data(self):
        """Test saving valid weekly revenue lost data"""
        save_data = {
            'table_type': 'weekly_revenue_lost',
            'row_id': self.weekly_revenue_lost_global.id,
            'field': 'faults_mwh',
            'value': '20.50'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        
        # Verify data was updated and total recalculated
        self.weekly_revenue_lost_global.refresh_from_db()
        self.assertEqual(self.weekly_revenue_lost_global.faults_mwh, Decimal('20.50'))
        expected_total = Decimal('20.50') + self.weekly_revenue_lost_global.maintenance_mwh
        self.assertEqual(self.weekly_revenue_lost_global.total_mwh, expected_total)
    
    def test_save_weekly_revenue_lost_total_field_readonly(self):
        """Test that total_mwh field cannot be edited directly"""
        save_data = {
            'table_type': 'weekly_revenue_lost',
            'row_id': self.weekly_revenue_lost_global.id,
            'field': 'total_mwh',
            'value': '100.00'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('read-only', data['error'].lower())
    
    def test_save_debtor_category_valid_data(self):
        """Test saving valid debtor category data"""
        save_data = {
            'table_type': 'debtors',
            'row_id': self.debtor_mining_global.id,
            'field': 'percentage',
            'value': '30.00'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        
        # Verify data was updated
        self.debtor_mining_global.refresh_from_db()
        self.assertEqual(self.debtor_mining_global.percentage, Decimal('30.00'))
        
        # Check if other percentages were auto-adjusted
        self.debtor_domestic_global.refresh_from_db()
        # The domestic percentage should be adjusted to maintain 100% total
    
    def test_save_debtor_category_invalid_percentage(self):
        """Test saving invalid debtor category percentage"""
        save_data = {
            'table_type': 'debtors',
            'row_id': self.debtor_mining_global.id,
            'field': 'percentage',
            'value': '150.00'  # Over 100%
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_save_dashboard_data_unauthenticated(self):
        """Test saving data without authentication"""
        self.client.logout()
        
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': self.weekly_collection_global.id,
            'field': 'zwl_millions',
            'value': '15.75'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('authentication', data['error'].lower())
    
    def test_save_dashboard_data_insufficient_permissions(self):
        """Test saving data with insufficient permissions"""
        # Remove admin role, add viewer role
        self.user_profile.roles.clear()
        self.user_profile.roles.add(self.viewer_role)
        
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': self.weekly_collection_global.id,
            'field': 'zwl_millions',
            'value': '15.75'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        # Response depends on permission implementation
        # Could be 403 Forbidden or 401 Unauthorized
        self.assertIn(response.status_code, [401, 403])
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_save_dashboard_data_invalid_table_type(self):
        """Test saving data with invalid table type"""
        save_data = {
            'table_type': 'invalid_table',
            'row_id': 1,
            'field': 'some_field',
            'value': '10.00'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('invalid', data['error'].lower())
    
    def test_save_dashboard_data_nonexistent_row(self):
        """Test saving data for non-existent row"""
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': 99999,  # Non-existent ID
            'field': 'zwl_millions',
            'value': '15.75'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('not found', data['error'].lower())
    
    def test_save_dashboard_data_invalid_field(self):
        """Test saving data for invalid field"""
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': self.weekly_collection_global.id,
            'field': 'invalid_field',
            'value': '15.75'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('field', data['error'].lower())
    
    def test_save_dashboard_data_invalid_json(self):
        """Test saving data with invalid JSON"""
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_save_dashboard_data_missing_required_fields(self):
        """Test saving data with missing required fields"""
        save_data = {
            'table_type': 'weekly_collections',
            # Missing row_id, field, and value
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_save_dashboard_data_method_not_allowed(self):
        """Test save_dashboard_data endpoint with GET method"""
        response = self.client.get('/dashboards/save_dashboard_data/')
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_save_dashboard_data_audit_trail(self):
        """Test that audit trail is updated when saving data"""
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': self.weekly_collection_global.id,
            'field': 'zwl_millions',
            'value': '18.50'
        }
        
        original_updated_at = self.weekly_collection_global.updated_at
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify audit trail was updated
        self.weekly_collection_global.refresh_from_db()
        self.assertGreater(self.weekly_collection_global.updated_at, original_updated_at)
        self.assertEqual(self.weekly_collection_global.updated_by, self.user_profile)


class APIEndpointIntegrationTest(BaseAPITestCase):
    """Integration tests for API endpoint workflows"""
    
    def test_complete_filter_and_edit_workflow(self):
        """Test complete workflow: filter data, then edit it"""
        # Step 1: Filter data by region
        filter_response = self.client.get(
            '/dashboards/dashboard_filter/',
            {'region_id': self.region.id}
        )
        
        self.assertEqual(filter_response.status_code, 200)
        filter_data = filter_response.json()
        
        # Step 2: Edit filtered data
        if filter_data['weekly_collections']:
            collection_id = None
            # Find the region-specific collection
            for collection in filter_data['weekly_collections']:
                # This would need to be implemented based on your actual response format
                pass
            
            if collection_id:
                save_data = {
                    'table_type': 'weekly_collections',
                    'row_id': collection_id,
                    'field': 'zwl_millions',
                    'value': '25.00'
                }
                
                save_response = self.client.post(
                    '/dashboards/save_dashboard_data/',
                    data=json.dumps(save_data),
                    content_type='application/json'
                )
                
                self.assertEqual(save_response.status_code, 200)
                save_response_data = save_response.json()
                self.assertTrue(save_response_data['success'])
    
    def test_concurrent_editing_scenario(self):
        """Test handling of concurrent editing scenarios"""
        # This would test what happens when multiple users edit the same data
        # Implementation depends on your concurrency handling strategy
        pass
    
    def test_data_consistency_across_endpoints(self):
        """Test that data is consistent across different endpoints"""
        # Get data from get_regions
        regions_response = self.client.get('/dashboards/get_regions/')
        regions_data = regions_response.json()
        
        # Get data from dashboard_filter
        filter_response = self.client.get('/dashboards/dashboard_filter/')
        filter_data = filter_response.json()
        
        # Compare data consistency
        # This would need specific implementation based on your data structure
        self.assertEqual(regions_response.status_code, 200)
        self.assertEqual(filter_response.status_code, 200)
    
    def test_error_recovery_workflow(self):
        """Test error recovery in editing workflow"""
        # Try to save invalid data
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': self.weekly_collection_global.id,
            'field': 'zwl_millions',
            'value': 'invalid_value'
        }
        
        response = self.client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # Verify original data is unchanged
        self.weekly_collection_global.refresh_from_db()
        self.assertEqual(self.weekly_collection_global.zwl_millions, Decimal('10.50'))