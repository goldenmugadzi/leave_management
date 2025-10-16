"""
Performance tests for change_requests views
"""
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.db import connection
from django.utils import timezone
from it.change_requests.models import ChangeRequest, CRApproval
from it.change_requests.views import get_change_requests_optimized, get_filtered_records
from it.users.models import UserProfile, Regions, CostCenter, Designations, Roles, Application, Responsibilities


class PerformanceTest(TransactionTestCase):
    """Performance tests for query optimization"""
    
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
        for i in range(100):
            cr = ChangeRequest.objects.create(
                cr_id=f"CR{i:03d}",
                change_type="New Profile",
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
    
    def test_query_count_optimization(self):
        """Test that optimized query reduces database hits"""
        with self.assertNumQueries(1):  # Should be 1 query instead of N+1
            records = get_change_requests_optimized(self.user)
            list(records)  # Force evaluation
    
    def test_prefetch_related_works(self):
        """Test that prefetch_related eliminates additional queries"""
        records = get_change_requests_optimized(self.user)
        
        # Accessing related data should not trigger additional queries
        with self.assertNumQueries(0):
            for record in records:
                _ = record.created_by.first_name
                _ = record.cost_center.name
                _ = record.region.region
    
    def test_computed_properties_performance(self):
        """Test that computed properties don't cause additional queries"""
        records = get_change_requests_optimized(self.user)
        
        # Accessing computed properties should not trigger additional queries
        with self.assertNumQueries(0):
            for record in records:
                _ = record.overall_status
                _ = record.status_display
                _ = record.status_color_class
                _ = record.change_type_config
    
    def test_filtered_records_performance(self):
        """Test performance of filtered records function"""
        # Test different view types
        view_types = ["incoming_cr", "delegation_requests", "active_delegations"]
        
        for view_type in view_types:
            with self.assertNumQueries(1):
                records = get_filtered_records(self.user, view_type)
                list(records)  # Force evaluation
    
    def test_large_dataset_performance(self):
        """Test performance with larger dataset"""
        # Create more records
        for i in range(100, 500):
            ChangeRequest.objects.create(
                cr_id=f"CR{i:03d}",
                change_type="Profile Modification",
                created_by=self.user,
                region=self.region,
                cost_center=self.cost_center,
                creator_designation=self.designation
            )
        
        # Should still be efficient
        with self.assertNumQueries(1):
            records = get_change_requests_optimized(self.user)
            list(records)  # Force evaluation


class QueryOptimizationTest(TestCase):
    """Test query optimization techniques"""
    
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
        
        # Create test change request
        self.change_request = ChangeRequest.objects.create(
            cr_id="CR001",
            change_type="New Profile",
            created_by=self.user,
            region=self.region,
            cost_center=self.cost_center,
            creator_designation=self.designation
        )
    
    def test_select_related_optimization(self):
        """Test that select_related reduces queries"""
        # Without optimization - this would cause N+1 queries
        records = ChangeRequest.objects.filter(region=self.user.region)
        
        # Count queries when accessing related fields
        with self.assertNumQueries(1):  # Should be 1 query with select_related
            for record in records:
                _ = record.created_by.first_name
                _ = record.cost_center.name
                _ = record.region.region
    
    def test_prefetch_related_optimization(self):
        """Test that prefetch_related reduces queries for reverse foreign keys"""
        # Create some approvals
        application = Application.objects.create(name='Test App', fullname='Test Application')
        sh_role = Roles.objects.create(
            app_id=application,
            role="section_head",
            description='Section Head Role'
        )
        
        for i in range(5):
            CRApproval.objects.create(
                cr_id=self.change_request,
                approver=self.user,
                approver_role=sh_role,
                approval_status=True,
                approval_date=timezone.now()
            )
        
        # Test prefetch_related
        records = ChangeRequest.objects.prefetch_related('crapproval_set').filter(region=self.user.region)
        
        with self.assertNumQueries(0):  # Should be 0 additional queries
            for record in records:
                approvals = list(record.crapproval_set.all())
                for approval in approvals:
                    _ = approval.approver.first_name
                    _ = approval.approver_role.role
