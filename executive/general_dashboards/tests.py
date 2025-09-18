from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
import json

from .models import WeeklyCollections, WeeklyRevenueLost, DebtorCategory
from .serializers import (
    WeeklyCollectionsSerializer, WeeklyRevenueLostSerializer, 
    DebtorCategorySerializer
)

User = get_user_model()


class GeneralDashboardsTestCase(TestCase):
    """Base test case for general dashboard tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create test locations
        from it.users.models import Regions, Districts, Depots
        
        self.region = Regions.objects.create(
            region="TEST REGION",
            code="TR"
        )
        
        self.district = Districts.objects.create(
            district="TEST DISTRICT",
            region_id=self.region.region,  # Use region_id as CharField
            code="TD"
        )
        
        self.depot = Depots.objects.create(
            depot="TEST DEPOT",
            district=self.district,
            region=self.region,
            code="TP"
        )
        
        # Create test data
        self.current_year = timezone.now().year
        self.current_month = timezone.now().month
        
        # Weekly Collections
        self.weekly_collection = WeeklyCollections.objects.create(
            week="Week 1",
            year=self.current_year,
            week_number=1,
            region=self.region,
            district=self.district,
            depot=self.depot,
            zwl_millions=10.50,
            usd_millions=5.25,
            updated_by=self.user
        )
        
        # Weekly Revenue Lost
        self.weekly_revenue_lost = WeeklyRevenueLost.objects.create(
            week="Week 1",
            year=self.current_year,
            week_number=1,
            region=self.region,
            faults_mwh=15.75,
            maintenance_mwh=8.25,
            updated_by=self.user
        )
        
        # Debtor Category
        self.debtor_category = DebtorCategory.objects.create(
            category="mining",
            year=self.current_year,
            month=self.current_month,
            region=self.region,
            district=self.district,
            depot=self.depot,
            percentage=25.00,
            updated_by=self.user
        )
        
        # Set up clients
        self.client = Client()
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)


class ModelsTestCase(GeneralDashboardsTestCase):
    """Test cases for models"""
    
    def test_weekly_collections_creation(self):
        """Test WeeklyCollections model creation"""
        collection = WeeklyCollections.objects.create(
            week="Week 2",
            year=self.current_year,
            week_number=2,
            region=self.region,
            zwl_millions=12.75,
            usd_millions=6.50,
            updated_by=self.user
        )
        
        self.assertEqual(collection.week, "Week 2")
        self.assertEqual(collection.zwl_millions, 12.75)
        self.assertEqual(collection.usd_millions, 6.50)
        self.assertEqual(collection.get_location_display(), "TEST REGION")
    
    def test_weekly_revenue_lost_auto_calculation(self):
        """Test that total_mwh is auto-calculated"""
        revenue_lost = WeeklyRevenueLost.objects.create(
            week="Week 2",
            year=self.current_year,
            week_number=2,
            region=self.region,
            faults_mwh=20.00,
            maintenance_mwh=10.00,
            updated_by=self.user
        )
        
        self.assertEqual(revenue_lost.total_mwh, 30.00)
    
    def test_debtor_category_validation(self):
        """Test DebtorCategory percentage validation"""
        # Create another category with 80% to test total validation
        DebtorCategory.objects.create(
            category="domestic",
            year=self.current_year,
            month=self.current_month,
            region=self.region,
            percentage=80.00,
            updated_by=self.user
        )
        
        # Try to create a category that would exceed 100%
        with self.assertRaises(Exception):
            DebtorCategory.objects.create(
                category="industry",
                year=self.current_year,
                month=self.current_month,
                region=self.region,
                percentage=25.00,  # This would make total 105%
                updated_by=self.user
            )
    
    def test_model_string_representations(self):
        """Test model __str__ methods"""
        self.assertIn("Week 1", str(self.weekly_collection))
        self.assertIn("Week 1", str(self.weekly_revenue_lost))
        self.assertIn("mining", str(self.debtor_category))
    
    def test_unique_constraints(self):
        """Test unique constraints"""
        # Try to create duplicate weekly collection
        with self.assertRaises(Exception):
            WeeklyCollections.objects.create(
                week="Week 1",
                year=self.current_year,
                week_number=1,
                region=self.region,
                district=self.district,
                depot=self.depot,
                zwl_millions=15.00,
                usd_millions=7.50,
                updated_by=self.user
            )


class SerializersTestCase(GeneralDashboardsTestCase):
    """Test cases for serializers"""
    
    def test_weekly_collections_serializer(self):
        """Test WeeklyCollectionsSerializer"""
        serializer = WeeklyCollectionsSerializer(self.weekly_collection)
        data = serializer.data
        
        self.assertEqual(data['week'], "Week 1")
        self.assertEqual(data['zwl_millions'], "10.50")
        self.assertEqual(data['usd_millions'], "5.25")
        self.assertEqual(data['region_name'], "TEST REGION")
        self.assertEqual(data['district_name'], "TEST DISTRICT")
        self.assertEqual(data['depot_name'], "TEST DEPOT")
    
    def test_weekly_revenue_lost_serializer(self):
        """Test WeeklyRevenueLostSerializer"""
        serializer = WeeklyRevenueLostSerializer(self.weekly_revenue_lost)
        data = serializer.data
        
        self.assertEqual(data['week'], "Week 1")
        self.assertEqual(data['faults_mwh'], "15.75")
        self.assertEqual(data['maintenance_mwh'], "8.25")
        self.assertEqual(data['total_mwh'], "24.00")
    
    def test_debtor_category_serializer(self):
        """Test DebtorCategorySerializer"""
        serializer = DebtorCategorySerializer(self.debtor_category)
        data = serializer.data
        
        self.assertEqual(data['category'], "mining")
        self.assertEqual(data['percentage'], "25.00")
        self.assertEqual(data['category_display'], "Mining")
    
    def test_serializer_validation(self):
        """Test serializer validation"""
        # Test invalid week format
        invalid_data = {
            'week': 'Invalid Week',
            'year': self.current_year,
            'week_number': 1,
            'region': self.region.id
        }
        
        serializer = WeeklyCollectionsSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('week', serializer.errors)
        
        # Test valid data
        valid_data = {
            'week': 'Week 3',
            'year': self.current_year,
            'week_number': 3,
            'region': self.region.id,
            'zwl_millions': 15.00,
            'usd_millions': 7.50
        }
        
        serializer = WeeklyCollectionsSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())


class ViewsTestCase(GeneralDashboardsTestCase):
    """Test cases for views"""
    
    def test_dashboard_index_view(self):
        """Test dashboard index view"""
        response = self.client.get(reverse('dashboards:dashboard_overview'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'general_dashboards/dashboard_index.html')
        self.assertContains(response, 'Executive Dashboard')
    
    def test_get_regions_view(self):
        """Test get_regions view"""
        response = self.api_client.get(reverse('dashboards:get_regions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST REGION')
        self.assertContains(response, 'TEST DISTRICT')
        self.assertContains(response, 'TEST DEPOT')
    
    def test_get_dashboard_data_view(self):
        """Test get_dashboard_data view"""
        response = self.api_client.get(reverse('dashboards:get_dashboard_data'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Weekly Collections')
        self.assertContains(response, 'Weekly Revenue Lost')
        self.assertContains(response, 'Debtors by Category')
        self.assertContains(response, 'ENERGY SOLD')
        self.assertContains(response, 'REVENUE COLLECTION')
    
    def test_get_dashboard_data_with_filters(self):
        """Test get_dashboard_data view with location filters"""
        # Test with region filter
        response = self.api_client.get(
            reverse('dashboards:get_dashboard_data'),
            {'region': self.region.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Week 1')
        
        # Test with district filter
        response = self.api_client.get(
            reverse('dashboards:get_dashboard_data'),
            {'district': self.district.id}
        )
        self.assertEqual(response.status_code, 200)
        
        # Test with depot filter
        response = self.api_client.get(
            reverse('dashboards:get_dashboard_data'),
            {'depot': self.depot.id}
        )
        self.assertEqual(response.status_code, 200)
    
    def test_save_dashboard_data_view(self):
        """Test save_dashboard_data view"""
        data = {
            'table': 'weekly_collections',
            'row': 0,
            'field': 'zwl_millions',
            'value': 15.75
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        # Verify the data was actually updated
        self.weekly_collection.refresh_from_db()
        self.assertEqual(self.weekly_collection.zwl_millions, 15.75)
    
    def test_save_weekly_revenue_lost(self):
        """Test saving weekly revenue lost data"""
        data = {
            'table': 'weekly_revenue_lost',
            'row': 0,
            'field': 'faults_mwh',
            'value': 25.50
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        # Verify total was auto-calculated
        self.weekly_revenue_lost.refresh_from_db()
        self.assertEqual(self.weekly_revenue_lost.faults_mwh, 25.50)
        self.assertEqual(self.weekly_revenue_lost.total_mwh, 33.75)  # 25.50 + 8.25
    
    def test_save_debtor_category(self):
        """Test saving debtor category data"""
        data = {
            'table': 'debtors',
            'row': 0,
            'field': 'percentage',
            'value': 30.00
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        # Verify the data was updated
        self.debtor_category.refresh_from_db()
        self.assertEqual(self.debtor_category.percentage, 30.00)
    
    def test_save_dashboard_data_validation_errors(self):
        """Test validation errors in save_dashboard_data"""
        # Test invalid table type
        data = {
            'table': 'invalid_table',
            'row': 0,
            'field': 'test_field',
            'value': 100
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        
        # Test missing required fields
        data = {
            'table': 'weekly_collections',
            'field': 'zwl_millions'
            # Missing 'row' and 'value'
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
    
    def test_get_user_permissions_view(self):
        """Test get_user_permissions view"""
        response = self.api_client.get(reverse('dashboards:get_user_permissions'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertIn('canEdit', response.data)
        self.assertIn('userRoles', response.data)
        self.assertIn('user', response.data)
    
    def test_create_sample_data_view(self):
        """Test create_sample_data view"""
        response = self.api_client.post(reverse('dashboards:create_sample_data'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        # Verify sample data was created
        self.assertGreater(WeeklyCollections.objects.count(), 1)
        self.assertGreater(WeeklyRevenueLost.objects.count(), 1)
        self.assertGreater(DebtorCategory.objects.count(), 1)


class APIIntegrationTestCase(GeneralDashboardsTestCase):
    """Test cases for API integration"""
    
    def test_dashboard_data_structure(self):
        """Test that dashboard data has the correct structure"""
        response = self.api_client.get(reverse('dashboards:get_dashboard_data'))
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected HTML structure
        content = response.content.decode()
        self.assertIn('metric-card', content)
        self.assertIn('dashboard-grid', content)
        self.assertIn('dashboard-section', content)
        self.assertIn('data-table', content)
    
    def test_htmx_integration(self):
        """Test HTMX integration for dynamic updates"""
        # Test that the dashboard template includes HTMX
        response = self.client.get(reverse('dashboards:dashboard_overview'))
        self.assertContains(response, 'htmx.org')
        
        # Test that the dashboard data endpoint returns HTML fragments
        response = self.api_client.get(reverse('dashboards:get_dashboard_data'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.get('Content-Type', ''))
    
    def test_filter_functionality(self):
        """Test location-based filtering functionality"""
        # Create data for different locations
        other_region = Regions.objects.create(region="OTHER REGION", code="OR")
        other_collection = WeeklyCollections.objects.create(
            week="Week 2",
            year=self.current_year,
            week_number=2,
            region=other_region,
            zwl_millions=20.00,
            usd_millions=10.00,
            updated_by=self.user
        )
        
        # Test filtering by region
        response = self.api_client.get(
            reverse('dashboards:get_dashboard_data'),
            {'region': self.region.id}
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Week 1', content)  # Should contain our test data
        self.assertNotIn('Week 2', content)  # Should not contain other region data
        
        # Test filtering by other region
        response = self.api_client.get(
            reverse('dashboards:get_dashboard_data'),
            {'region': other_region.id}
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Week 2', content)  # Should contain other region data
        self.assertNotIn('Week 1', content)  # Should not contain our test data


class PerformanceTestCase(GeneralDashboardsTestCase):
    """Test cases for performance and scalability"""
    
    def test_large_dataset_performance(self):
        """Test performance with larger datasets"""
        # Create multiple records to test performance
        for i in range(52):  # Full year of weekly data
            WeeklyCollections.objects.create(
                week=f"Week {i+1}",
                year=self.current_year,
                week_number=i+1,
                region=self.region,
                zwl_millions=10.00 + i,
                usd_millions=5.00 + i,
                updated_by=self.user
            )
        
        # Test that the dashboard can handle larger datasets
        start_time = timezone.now()
        response = self.api_client.get(reverse('dashboards:get_dashboard_data'))
        end_time = timezone.now()
        
        self.assertEqual(response.status_code, 200)
        
        # Response time should be reasonable (less than 1 second)
        response_time = (end_time - start_time).total_seconds()
        self.assertLess(response_time, 1.0)
        
        # Verify all data is included
        content = response.content.decode()
        self.assertIn('Week 1', content)
        self.assertIn('Week 52', content)
    
    def test_concurrent_editing(self):
        """Test concurrent editing scenarios"""
        # Simulate multiple users editing the same data
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123',
            email='other@example.com'
        )
        
        # First user edits
        data1 = {
            'table': 'weekly_collections',
            'row': 0,
            'field': 'zwl_millions',
            'value': 25.00
        }
        
        response1 = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data1,
            format='json'
        )
        self.assertEqual(response1.status_code, 200)
        
        # Second user edits the same field
        other_api_client = APIClient()
        other_api_client.force_authenticate(user=other_user)
        
        data2 = {
            'table': 'weekly_collections',
            'row': 0,
            'field': 'zwl_millions',
            'value': 30.00
        }
        
        response2 = other_api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data2,
            format='json'
        )
        self.assertEqual(response2.status_code, 200)
        
        # Verify the final state
        self.weekly_collection.refresh_from_db()
        self.assertEqual(self.weekly_collection.zwl_millions, 30.00)


class SecurityTestCase(GeneralDashboardsTestCase):
    """Test cases for security and permissions"""
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected endpoints"""
        # Test save endpoint without authentication
        data = {
            'table': 'weekly_collections',
            'row': 0,
            'field': 'zwl_millions',
            'value': 100.00
        }
        
        response = self.client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            content_type='application/json'
        )
        self.assertIn(response.status_code, [401, 403])  # Should require authentication
        
        # Test user permissions endpoint without authentication
        response = self.client.get(reverse('dashboards:get_user_permissions'))
        self.assertIn(response.status_code, [401, 403])
    
    def test_authorized_user_permissions(self):
        """Test that authorized users can access protected endpoints"""
        # Test with authenticated user
        response = self.api_client.get(reverse('dashboards:get_user_permissions'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
    
    def test_data_validation_security(self):
        """Test that data validation prevents malicious input"""
        # Test SQL injection attempts
        malicious_data = {
            'table': 'weekly_collections; DROP TABLE general_dashboards_weeklycollections; --',
            'row': 0,
            'field': 'zwl_millions',
            'value': 100.00
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            malicious_data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)  # Should reject invalid table name
        
        # Test XSS attempts
        malicious_data = {
            'table': 'weekly_collections',
            'row': 0,
            'field': 'zwl_millions',
            'value': '<script>alert("xss")</script>'
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            malicious_data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)  # Should reject non-numeric values


class EdgeCaseTestCase(GeneralDashboardsTestCase):
    """Test cases for edge cases and error conditions"""
    
    def test_empty_data_handling(self):
        """Test handling of empty datasets"""
        # Clear all test data
        WeeklyCollections.objects.all().delete()
        WeeklyRevenueLost.objects.all().delete()
        DebtorCategory.objects.all().delete()
        
        # Test that dashboard handles empty data gracefully
        response = self.api_client.get(reverse('dashboards:get_dashboard_data'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        self.assertIn('No data available', content)
    
    def test_invalid_location_filters(self):
        """Test handling of invalid location filters"""
        # Test with non-existent IDs
        response = self.api_client.get(
            reverse('dashboards:get_dashboard_data'),
            {'region': 99999, 'district': 88888, 'depot': 77777}
        )
        self.assertEqual(response.status_code, 200)
        
        # Should return empty data gracefully
        content = response.content.decode()
        self.assertIn('No data available', content)
    
    def test_boundary_values(self):
        """Test boundary value handling"""
        # Test maximum percentage for debtors
        data = {
            'table': 'debtors',
            'row': 0,
            'field': 'percentage',
            'value': 100.00
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Test minimum values
        data = {
            'table': 'weekly_collections',
            'row': 0,
            'field': 'zwl_millions',
            'value': 0.00
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Test negative values (should be rejected)
        data = {
            'table': 'weekly_collections',
            'row': 0,
            'field': 'zwl_millions',
            'value': -10.00
        }
        
        response = self.api_client.post(
            reverse('dashboards:save_dashboard_data'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)  # Should reject negative values
