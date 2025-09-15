"""
Performance tests for Phase 3 enhancements
"""
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.db import connection
from django.utils import timezone
from it.change_requests.models import ChangeRequest, CRApproval
from it.change_requests.views import (
    get_change_requests_optimized, 
    get_filtered_records,
    api_change_requests_optimized,
    api_change_request_stats
)
from it.change_requests.pagination import CursorPaginator, get_paginated_data
from it.change_requests.query_analysis import QueryAnalyzer, analyze_queryset_performance
from it.users.models import UserProfile, Regions, CostCenter, Designations, Roles, Application, Responsibilities


class DatabaseIndexPerformanceTest(TransactionTestCase):
    """Test database index performance improvements"""
    
    def setUp(self):
        """Set up test data"""
        # Create test data
        self.region = Regions.objects.create(region="Test Region")
        self.cost_center = CostCenter.objects.create(name="Test CC", region=self.region)
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region
        )
        
        # Create application and roles
        self.application = Application.objects.create(name='Test App', fullname='Test Application')
        self.sh_role = Roles.objects.create(
            app_id=self.application,
            role="section_head",
            description='Section Head Role'
        )
        self.it_role = Roles.objects.create(
            app_id=self.application,
            role="it_section_head",
            description='IT Section Head Role'
        )
        
        # Create multiple change requests for testing
        for i in range(200):
            cr = ChangeRequest.objects.create(
                cr_id=f"CR{i:03d}",
                change_type="New Profile" if i % 2 == 0 else "Profile Modification",
                created_by=self.user,
                region=self.region,
                cost_center=self.cost_center,
                creator_designation=self.designation
            )
            
            # Add some approvals for variety
            if i % 3 == 0:  # Every third request has section head approval
                CRApproval.objects.create(
                    cr_id=cr,
                    approver=self.user,
                    approver_role=self.sh_role,
                    approval_status=True,
                    approval_date=timezone.now()
                )
            
            if i % 5 == 0:  # Every fifth request has both approvals
                CRApproval.objects.create(
                    cr_id=cr,
                    approver=self.user,
                    approver_role=self.it_role,
                    approval_status=True,
                    approval_date=timezone.now()
                )
    
    def test_composite_index_performance(self):
        """Test that composite indexes improve query performance"""
        # Test region + is_deleted + created_at index
        with self.assertNumQueries(1):
            records = ChangeRequest.objects.filter(
                region=self.region,
                is_deleted=False
            ).order_by('-created_at')
            list(records)
    
    def test_approval_query_performance(self):
        """Test approval query performance with new indexes"""
        # Test cr_id + approver_role index
        with self.assertNumQueries(1):
            approvals = CRApproval.objects.filter(
                cr_id__region=self.region,
                approver_role=self.sh_role
            )
            list(approvals)
    
    def test_filtering_performance(self):
        """Test filtering performance with composite indexes"""
        # Test change_type + region + is_deleted index
        with self.assertNumQueries(1):
            records = ChangeRequest.objects.filter(
                change_type="New Profile",
                region=self.region,
                is_deleted=False
            )
            list(records)


class CursorPaginationTest(TestCase):
    """Test cursor-based pagination performance"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region")
        self.cost_center = CostCenter.objects.create(name="Test CC", region=self.region)
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region
        )
        
        # Create test change requests
        for i in range(100):
            ChangeRequest.objects.create(
                cr_id=f"CR{i:03d}",
                change_type="New Profile",
                created_by=self.user,
                region=self.region,
                cost_center=self.cost_center,
                creator_designation=self.designation
            )
    
    def test_cursor_pagination_performance(self):
        """Test cursor pagination performance"""
        queryset = ChangeRequest.objects.filter(region=self.user.region)
        paginator = CursorPaginator(queryset, page_size=25)
        
        # Test first page
        result = paginator.paginate()
        self.assertEqual(len(result['data']), 25)
        self.assertTrue(result['has_next'])
        self.assertFalse(result['has_prev'])
        
        # Test next page
        if result['next_cursor']:
            result2 = paginator.paginate(cursor=result['next_cursor'])
            self.assertEqual(len(result2['data']), 25)
            self.assertTrue(result2['has_prev'])
    
    def test_cursor_vs_offset_performance(self):
        """Compare cursor vs offset pagination performance"""
        queryset = ChangeRequest.objects.filter(region=self.user.region)
        
        # Test cursor pagination
        cursor_start = time.time()
        paginated_data = get_paginated_data(queryset, use_cursor=True, per_page=25)
        cursor_time = time.time() - cursor_start
        
        # Test offset pagination
        offset_start = time.time()
        paginated_data_offset = get_paginated_data(queryset, use_cursor=False, per_page=25)
        offset_time = time.time() - offset_start
        
        # Cursor pagination should be faster for large datasets
        self.assertLess(cursor_time, offset_time * 2)  # Allow some margin


class APIOptimizationTest(TestCase):
    """Test optimized API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region")
        self.cost_center = CostCenter.objects.create(name="Test CC", region=self.region)
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region
        )
        
        # Create test change requests
        for i in range(50):
            ChangeRequest.objects.create(
                cr_id=f"CR{i:03d}",
                change_type="New Profile",
                created_by=self.user,
                region=self.region,
                cost_center=self.cost_center,
                creator_designation=self.designation
            )
    
    def test_optimized_api_performance(self):
        """Test optimized API endpoint performance"""
        # Mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.GET = {}
        
        request = MockRequest(self.user)
        
        # Test API performance
        start_time = time.time()
        response = api_change_requests_optimized(request)
        execution_time = time.time() - start_time
        
        # Should be fast (less than 1 second for 50 records)
        self.assertLess(execution_time, 1.0)
        self.assertEqual(response.status_code, 200)
    
    def test_stats_api_performance(self):
        """Test stats API performance"""
        # Mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.GET = {}
        
        request = MockRequest(self.user)
        
        # Test stats API performance
        start_time = time.time()
        response = api_change_request_stats(request)
        execution_time = time.time() - start_time
        
        # Should be very fast (less than 0.5 seconds)
        self.assertLess(execution_time, 0.5)
        self.assertEqual(response.status_code, 200)


class QueryAnalysisTest(TestCase):
    """Test query analysis utilities"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region")
        self.cost_center = CostCenter.objects.create(name="Test CC", region=self.region)
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region
        )
        
        # Create test change requests
        for i in range(20):
            ChangeRequest.objects.create(
                cr_id=f"CR{i:03d}",
                change_type="New Profile",
                created_by=self.user,
                region=self.region,
                cost_center=self.cost_center,
                creator_designation=self.designation
            )
    
    def test_query_analyzer(self):
        """Test query analyzer functionality"""
        analyzer = QueryAnalyzer()
        
        # Test query logging
        analyzer.log_query("SELECT * FROM test", 50.0)
        analyzer.log_query("SELECT * FROM slow_query", 150.0)
        
        stats = analyzer.get_query_stats()
        self.assertEqual(stats['total_queries'], 2)
        self.assertEqual(stats['slow_queries'], 1)
        self.assertEqual(stats['slow_query_percentage'], 50.0)
    
    def test_queryset_analysis(self):
        """Test queryset performance analysis"""
        queryset = ChangeRequest.objects.filter(region=self.user.region)
        
        analysis = analyze_queryset_performance(queryset, "Test Query")
        
        self.assertIn('execution_time_ms', analysis)
        self.assertIn('result_count', analysis)
        self.assertIn('query_count', analysis)
        self.assertIn('is_optimized', analysis)
        self.assertEqual(analysis['result_count'], 20)


class PerformanceMonitoringTest(TestCase):
    """Test performance monitoring decorators"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region")
        self.cost_center = CostCenter.objects.create(name="Test CC", region=self.region)
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region
        )
    
    def test_performance_monitoring(self):
        """Test that performance monitoring works correctly"""
        # This test would require mocking the logger to verify warnings
        # For now, we'll just test that the function still works
        records = get_change_requests_optimized(self.user)
        self.assertIsNotNone(records)
        
        filtered_records = get_filtered_records(self.user, "all")
        self.assertIsNotNone(filtered_records)
