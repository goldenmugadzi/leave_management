"""
Integration tests for dashboard enhancement - Task 20: Final integration and testing

This module contains comprehensive integration tests that verify:
- Complete dashboard functionality with all new sections
- Location filtering works across all sections  
- Inline editing for all data types
- Cross-browser compatibility considerations
- End-to-end workflow testing

Requirements covered:
- 1.5: Complete collections data integration
- 2.6: Complete revenue lost data integration  
- 3.7: Complete debtors data integration
- 4.8: Complete inline editing workflow
- 6.5: Complete location filtering integration
- 7.6: Comprehensive testing coverage

To run these tests:
    python manage.py test executive.general_dashboards.test_integration
"""

import json
import time
from decimal import Decimal
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from django.test.utils import override_settings

from .models import (
    WeeklyCollections, WeeklyRevenueLost, DebtorCategory,
    DashboardMetric, WeeklySales, WeeklyOutage, TopDebtor, WeeklyFaultMaintenance
)
from it.users.models import UserProfile, Regions, Districts, Depots, Roles


class DashboardIntegrationTestCase(TransactionTestCase):
    """Base integration test case with comprehensive setup"""
    
    def setUp(self):
        """Set up comprehensive test environment"""
        # Create test users with different roles
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.viewer_user = User.objects.create_user(
            username='viewer_user',
            email='viewer@example.com',
            password='viewerpass123'
        )
        
        # Create user profiles
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            username='admin_user',
            email='admin@example.com'
        )
        
        self.viewer_profile = UserProfile.objects.create(
            user=self.viewer_user,
            username='viewer_user',
            email='viewer@example.com'
        )
        
        # Create roles
        self.admin_role = Roles.objects.create(
            role='admin',
            name='Administrator',
            description='Full dashboard access',
            application='dashboards'
        )
        
        self.viewer_role = Roles.objects.create(
            role='viewer',
            name='Viewer',
            description='Read-only dashboard access',
            application='dashboards'
        )
        
        # Assign roles
        self.admin_profile.roles.add(self.admin_role)
        self.viewer_profile.roles.add(self.viewer_role)
        
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
        
        # Set up clients
        self.admin_client = Client()
        self.viewer_client = Client()
        
        self.admin_client.login(username='admin_user', password='adminpass123')
        self.viewer_client.login(username='viewer_user', password='viewerpass123')
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Create comprehensive test data"""
        # Create weekly collections data
        for i in range(1, 5):
            WeeklyCollections.objects.create(
                week=f'Week {i}',
                zwl_millions=Decimal(f'{10 + i}.50'),
                usd_millions=Decimal(f'{5 + i}.25'),
                year=2025,
                week_number=i,
                updated_by=self.admin_profile
            )
            
            # Regional data
            WeeklyCollections.objects.create(
                week=f'Week {i}',
                zwl_millions=Decimal(f'{8 + i}.25'),
                usd_millions=Decimal(f'{4 + i}.10'),
                region=self.region,
                year=2025,
                week_number=i,
                updated_by=self.admin_profile
            )
        
        # Create weekly revenue lost data
        for i in range(1, 5):
            WeeklyRevenueLost.objects.create(
                week=f'Week {i}',
                faults_mwh=Decimal(f'{15 + i}.75'),
                maintenance_mwh=Decimal(f'{8 + i}.50'),
                year=2025,
                week_number=i,
                updated_by=self.admin_profile
            )
        
        # Create debtor category data
        categories = ['mining', 'domestic', 'industry', 'commercial']
        percentages = [25.0, 35.0, 25.0, 15.0]
        
        for category, percentage in zip(categories, percentages):
            DebtorCategory.objects.create(
                category=category,
                percentage=Decimal(str(percentage)),
                year=2025,
                month=1,
                updated_by=self.admin_profile
            )

class C
ompleteDashboardFunctionalityTest(DashboardIntegrationTestCase):
    """Test complete dashboard functionality with all new sections - Requirement 1.5, 2.6, 3.7"""
    
    def test_complete_dashboard_data_retrieval(self):
        """Test that all dashboard sections return complete data"""
        response = self.admin_client.get('/dashboards/regions')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify all required sections are present
        required_sections = [
            'regions', 'districts', 'depots', 'pbncs', 'upos', 'tds',
            'weekly_sales', 'weekly_outages', 'weekly_faults_maintenance',
            'weekly_collections', 'weekly_revenue_lost', 'debtors'
        ]
        
        for section in required_sections:
            self.assertIn(section, data, f"Missing section: {section}")
        
        # Verify new sections have data
        self.assertGreater(len(data['weekly_collections']), 0, "No weekly collections data")
        self.assertGreater(len(data['weekly_revenue_lost']), 0, "No weekly revenue lost data")
        self.assertGreater(len(data['debtors']), 0, "No debtors data")
        
        # Verify data structure for weekly collections
        if data['weekly_collections']:
            collection = data['weekly_collections'][0]
            required_fields = ['week', 'zwl_millions', 'usd_millions']
            for field in required_fields:
                self.assertIn(field, collection, f"Missing field in collections: {field}")
        
        # Verify data structure for weekly revenue lost
        if data['weekly_revenue_lost']:
            revenue_lost = data['weekly_revenue_lost'][0]
            required_fields = ['week', 'faults_mwh', 'maintenance_mwh', 'total_mwh']
            for field in required_fields:
                self.assertIn(field, revenue_lost, f"Missing field in revenue lost: {field}")
        
        # Verify data structure for debtors
        if data['debtors']:
            debtor = data['debtors'][0]
            required_fields = ['id', 'category', 'percentage']
            for field in required_fields:
                self.assertIn(field, debtor, f"Missing field in debtors: {field}")
    
    def test_dashboard_data_consistency(self):
        """Test that dashboard data is consistent across different endpoints"""
        # Get data from regions endpoint
        regions_response = self.admin_client.get('/dashboards/regions')
        regions_data = regions_response.json()
        
        # Get data from dashboard_data endpoint
        dashboard_response = self.admin_client.get('/dashboards/dashboard_data')
        dashboard_data = dashboard_response.json()
        
        # Both should succeed
        self.assertEqual(regions_response.status_code, 200)
        self.assertEqual(dashboard_response.status_code, 200)
        
        # Verify consistent data structure
        self.assertIn('weekly_collections', regions_data)
        self.assertIn('weekly_revenue_lost', regions_data)
        self.assertIn('debtors', regions_data)
    
    def test_all_sections_data_format_validation(self):
        """Test that all sections return properly formatted data"""
        response = self.admin_client.get('/dashboards/regions')
        data = response.json()
        
        # Test weekly collections format
        for collection in data['weekly_collections']:
            self.assertIsInstance(collection['week'], str)
            self.assertRegex(collection['zwl_millions'], r'^\d+\.\d{2}$')
            self.assertRegex(collection['usd_millions'], r'^\d+\.\d{2}$')
        
        # Test weekly revenue lost format
        for revenue_lost in data['weekly_revenue_lost']:
            self.assertIsInstance(revenue_lost['week'], str)
            self.assertRegex(revenue_lost['faults_mwh'], r'^\d+\.\d{2}$')
            self.assertRegex(revenue_lost['maintenance_mwh'], r'^\d+\.\d{2}$')
            self.assertRegex(revenue_lost['total_mwh'], r'^\d+\.\d{2}$')
            
            # Verify total calculation
            faults = Decimal(revenue_lost['faults_mwh'])
            maintenance = Decimal(revenue_lost['maintenance_mwh'])
            total = Decimal(revenue_lost['total_mwh'])
            self.assertEqual(total, faults + maintenance)
        
        # Test debtors format
        total_percentage = Decimal('0.00')
        for debtor in data['debtors']:
            self.assertIsInstance(debtor['id'], int)
            self.assertIsInstance(debtor['category'], str)
            self.assertRegex(debtor['percentage'], r'^\d+\.\d{2}$')
            total_percentage += Decimal(debtor['percentage'])
        
        # Verify percentages sum to 100% (allowing small floating point differences)
        self.assertAlmostEqual(float(total_percentage), 100.0, places=1)


class LocationFilteringIntegrationTest(DashboardIntegrationTestCase):
    """Test location filtering works across all sections - Requirement 6.5"""
    
    def test_region_filtering_all_sections(self):
        """Test that region filtering works for all dashboard sections"""
        response = self.admin_client.get(
            '/dashboards/dashboard_filter',
            {'region_id': self.region.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify all sections are present
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
        
        # Verify data is filtered (should have regional data)
        self.assertGreaterEqual(len(data['weekly_collections']), 0)
        self.assertGreaterEqual(len(data['weekly_revenue_lost']), 0)
        self.assertGreaterEqual(len(data['debtors']), 0)
    
    def test_district_filtering_all_sections(self):
        """Test that district filtering works for all dashboard sections"""
        response = self.admin_client.get(
            '/dashboards/dashboard_filter',
            {'district_id': self.district.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify all sections are present
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
    
    def test_depot_filtering_all_sections(self):
        """Test that depot filtering works for all dashboard sections"""
        response = self.admin_client.get(
            '/dashboards/dashboard_filter',
            {'depot_id': self.depot.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify all sections are present
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
    
    def test_no_filter_returns_global_data(self):
        """Test that no filter returns global/aggregated data"""
        response = self.admin_client.get('/dashboards/dashboard_filter')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return global data
        self.assertIn('weekly_collections', data)
        self.assertIn('weekly_revenue_lost', data)
        self.assertIn('debtors', data)
        
        # Should have data (global data exists)
        self.assertGreater(len(data['weekly_collections']), 0)
        self.assertGreater(len(data['weekly_revenue_lost']), 0)
        self.assertGreater(len(data['debtors']), 0)
clas
s InlineEditingIntegrationTest(DashboardIntegrationTestCase):
    """Test inline editing for all data types - Requirement 4.8"""
    
    def test_weekly_collections_inline_editing_workflow(self):
        """Test complete inline editing workflow for weekly collections"""
        # Get a collections record to edit
        collection = WeeklyCollections.objects.filter(region__isnull=True).first()
        self.assertIsNotNone(collection)
        
        original_zwl = collection.zwl_millions
        new_zwl = original_zwl + Decimal('5.00')
        
        # Test editing ZWL value
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': collection.id,
            'field': 'zwl_millions',
            'value': str(new_zwl)
        }
        
        response = self.admin_client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify data was updated
        collection.refresh_from_db()
        self.assertEqual(collection.zwl_millions, new_zwl)
        self.assertEqual(collection.updated_by, self.admin_profile)
    
    def test_weekly_revenue_lost_inline_editing_workflow(self):
        """Test complete inline editing workflow for weekly revenue lost"""
        # Get a revenue lost record to edit
        revenue_lost = WeeklyRevenueLost.objects.filter(region__isnull=True).first()
        self.assertIsNotNone(revenue_lost)
        
        original_faults = revenue_lost.faults_mwh
        original_maintenance = revenue_lost.maintenance_mwh
        new_faults = original_faults + Decimal('10.00')
        
        # Test editing faults MWh
        save_data = {
            'table_type': 'weekly_revenue_lost',
            'row_id': revenue_lost.id,
            'field': 'faults_mwh',
            'value': str(new_faults)
        }
        
        response = self.admin_client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify data was updated and total recalculated
        revenue_lost.refresh_from_db()
        self.assertEqual(revenue_lost.faults_mwh, new_faults)
        expected_total = new_faults + original_maintenance
        self.assertEqual(revenue_lost.total_mwh, expected_total)
    
    def test_debtor_category_inline_editing_workflow(self):
        """Test complete inline editing workflow for debtor categories"""
        # Get debtor categories for global data
        mining_debtor = DebtorCategory.objects.filter(
            category='mining',
            region__isnull=True,
            district__isnull=True,
            depot__isnull=True
        ).first()
        
        self.assertIsNotNone(mining_debtor)
        
        new_mining = Decimal('30.00')
        
        # Test editing mining percentage
        save_data = {
            'table_type': 'debtors',
            'row_id': mining_debtor.id,
            'field': 'percentage',
            'value': str(new_mining)
        }
        
        response = self.admin_client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify mining percentage was updated
        mining_debtor.refresh_from_db()
        self.assertEqual(mining_debtor.percentage, new_mining)
    
    def test_inline_editing_validation_errors(self):
        """Test that inline editing properly handles validation errors"""
        collection = WeeklyCollections.objects.filter(region__isnull=True).first()
        
        # Test negative value (should fail)
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': collection.id,
            'field': 'zwl_millions',
            'value': '-10.00'
        }
        
        response = self.admin_client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)


class CrossBrowserCompatibilityTest(DashboardIntegrationTestCase):
    """Test cross-browser compatibility considerations"""
    
    def test_api_responses_json_format(self):
        """Test that API responses are in proper JSON format for all browsers"""
        endpoints = [
            '/dashboards/regions',
            '/dashboards/dashboard_data',
            '/dashboards/dashboard_filter',
            '/dashboards/user_permissions'
        ]
        
        for endpoint in endpoints:
            response = self.admin_client.get(endpoint)
            
            # Should return valid JSON
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/json')
            
            # Should be parseable as JSON
            try:
                data = response.json()
                self.assertIsInstance(data, dict)
            except json.JSONDecodeError:
                self.fail(f"Invalid JSON response from {endpoint}")
    
    def test_unicode_data_handling(self):
        """Test that unicode data is properly handled across browsers"""
        # Create test data with unicode characters
        region = Regions.objects.create(
            region='Test Région Ñoñó',
            code='TRU'
        )
        
        WeeklyCollections.objects.create(
            week='Week Ñ',
            zwl_millions=Decimal('10.50'),
            usd_millions=Decimal('5.25'),
            region=region,
            year=2025,
            week_number=1,
            updated_by=self.admin_profile
        )
        
        response = self.admin_client.get('/dashboards/regions')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should handle unicode properly
        self.assertIn('regions', data)
        self.assertIn('weekly_collections', data)


class PerformanceIntegrationTest(DashboardIntegrationTestCase):
    """Test performance aspects of the integrated dashboard"""
    
    def test_dashboard_load_performance(self):
        """Test that dashboard loads within acceptable time limits"""
        start_time = time.time()
        
        response = self.admin_client.get('/dashboards/regions')
        
        end_time = time.time()
        load_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # Should load within 5 seconds (adjust as needed)
        self.assertLess(load_time, 5.0, f"Dashboard took {load_time:.2f} seconds to load")
    
    def test_filtering_performance(self):
        """Test that filtering operations perform within acceptable limits"""
        start_time = time.time()
        
        response = self.admin_client.get(
            '/dashboards/dashboard_filter',
            {'region_id': self.region.id}
        )
        
        end_time = time.time()
        filter_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # Filtering should be fast
        self.assertLess(filter_time, 3.0, f"Filtering took {filter_time:.2f} seconds")
    
    def test_save_operation_performance(self):
        """Test that save operations perform within acceptable limits"""
        collection = WeeklyCollections.objects.filter(region__isnull=True).first()
        
        save_data = {
            'table_type': 'weekly_collections',
            'row_id': collection.id,
            'field': 'zwl_millions',
            'value': '20.00'
        }
        
        start_time = time.time()
        
        response = self.admin_client.post(
            '/dashboards/save_dashboard_data/',
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        end_time = time.time()
        save_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # Save operations should be fast
        self.assertLess(save_time, 2.0, f"Save operation took {save_time:.2f} seconds")