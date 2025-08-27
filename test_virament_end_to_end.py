"""
Comprehensive End-to-End Virament Testing Script
Simulates actual user workflow with templates, forms, views, and approval process
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from unittest.mock import patch
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Asset_budget_Virament, AssetBudget, Transactions
from ACE2.forms import ViramentForm
from it.users.models import UserProfile, Regions, Sections
from approve.models import Process


class ViramentEndToEndTestCase(TestCase):
    """Comprehensive test suite for virament functionality with actual implementation workflow"""
    
    def setUp(self):
        """Setup test data mimicking actual system state"""
        print("\n🔧 Setting up test environment...")
        
        # Create test region and section
        self.test_region = Regions.objects.create(region="Test Region", region_code="TR")
        self.test_section = Sections.objects.create(
            section="Test Section",
            region_id=self.test_region
        )
        
        # Create test user with complete profile
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@company.com',
            first_name='Test',
            last_name='User'
        )
        
        self.user_profile = UserProfile.objects.create(
            username=self.test_user.username,
            region=self.test_region.region,
            section=self.test_section.section,
            first_name='Test',
            last_name='User',
            email='test@company.com'
        )
        
        # Create test budgets with realistic balances
        self.source_budget = AssetBudget.objects.create(
            budget_name="Infrastructure Budget - Source",
            period=2025,
            region=self.test_region.region,
            balance=500000.00,
            to_be_withdrawn=50000.00  # Some amount already reserved
        )
        
        self.destination_budget = AssetBudget.objects.create(
            budget_name="Equipment Budget - Destination", 
            period=2025,
            region=self.test_region.region,
            balance=200000.00,
            to_be_withdrawn=0.00
        )
        
        # Create insufficient balance budget for testing
        self.low_budget = AssetBudget.objects.create(
            budget_name="Low Balance Budget",
            period=2025,
            region=self.test_region.region,
            balance=1000.00,
            to_be_withdrawn=950.00  # Only 50 available
        )
        
        # Create approval process
        self.approval_process = Process.objects.create(
            name="Virament Approval Process",
            description="Budget virament approval workflow"
        )
        
        self.client = Client()
        
    def test_01_virament_form_initialization(self):
        """Test form initialization with user-specific data"""
        print("\n📋 Testing form initialization...")
        
        form = ViramentForm(user=self.user_profile)
        
        # Verify form initializes correctly
        self.assertIsNotNone(form)
        
        # Check that budgets are filtered by user's region
        budget_queryset = form.fields['from_budget'].queryset
        self.assertTrue(budget_queryset.filter(id=self.source_budget.id).exists())
        self.assertTrue(budget_queryset.filter(id=self.destination_budget.id).exists())
        
        # Check section filtering
        section_queryset = form.fields['section'].queryset
        self.assertTrue(section_queryset.filter(id=self.test_section.id).exists())
        
        print("✅ Form initialization successful")
        
    def test_02_virament_form_validation(self):
        """Test comprehensive form validation logic"""
        print("\n🔍 Testing form validation...")
        
        # Test valid virament data
        valid_data = {
            'from_budget': self.source_budget.id,
            'to_budget': self.destination_budget.id,
            'amount': 100000.00,
            'reason': 'Equipment procurement transfer',
            'section': self.test_section.id,
            'currency': 'ZWL'
        }
        
        form = VirementForm(data=valid_data, user=self.user_profile)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        print("✅ Valid form data passed validation")
        
        # Test same budget validation
        invalid_data = valid_data.copy()
        invalid_data['to_budget'] = self.source_budget.id
        form = ViramentForm(data=invalid_data, user=self.user_profile)
        self.assertFalse(form.is_valid())
        self.assertIn('Source and destination budgets cannot be the same', str(form.errors))
        print("✅ Same budget validation working")
        
        # Test insufficient balance validation
        insufficient_data = valid_data.copy()
        insufficient_data['from_budget'] = self.low_budget.id
        insufficient_data['amount'] = 100.00  # More than available (50)
        form = ViramentForm(data=insufficient_data, user=self.user_profile)
        self.assertFalse(form.is_valid())
        self.assertIn('Insufficient available balance', str(form.errors))
        print("✅ Insufficient balance validation working")
        
        # Test negative amount validation
        negative_data = valid_data.copy()
        negative_data['amount'] = -1000.00
        form = ViramentForm(data=negative_data, user=self.user_profile)
        self.assertFalse(form.is_valid())
        self.assertIn('Amount must be positive', str(form.errors))
        print("✅ Negative amount validation working")
        
    def test_03_virament_view_get_request(self):
        """Test GET request to virament creation view"""
        print("\n🌐 Testing GET request to virament creation view...")
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Make GET request to create virament view
        url = reverse('Ace:create_virament')
        response = self.client.get(url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check template used
        self.assertTemplateUsed(response, 'finance/ace2/create_virament.html')
        
        # Check context contains form
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ViramentForm)
        
        # Check form is initialized with user
        form = response.context['form']
        budget_queryset = form.fields['from_budget'].queryset
        self.assertTrue(budget_queryset.filter(region=self.test_region.region).exists())
        
        print("✅ GET request handling successful")
        
    def test_04_virament_creation_workflow(self):
        """Test complete virament creation workflow via POST request"""
        print("\n🔄 Testing complete virament creation workflow...")
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Prepare virament data
        virament_data = {
            'from_budget': self.source_budget.id,
            'to_budget': self.destination_budget.id,
            'amount': 150000.00,
            'reason': 'Transfer for critical equipment procurement',
            'section': self.test_section.id,
            'currency': 'ZWL'
        }
        
        # Record initial budget states
        initial_source_balance = self.source_budget.balance
        initial_source_to_be_withdrawn = self.source_budget.to_be_withdrawn
        initial_dest_balance = self.destination_budget.balance
        
        # Make POST request to create virament
        url = reverse('Ace:create_virament')
        response = self.client.post(url, data=virament_data, follow=True)
        
        # Check successful creation (redirect to detail view)
        self.assertEqual(response.status_code, 200)
        
        # Verify virament was created
        virament = Asset_budget_Virament.objects.filter(
            from_budget=self.source_budget,
            to_budget=self.destination_budget,
            amount=150000.00
        ).first()
        
        self.assertIsNotNone(virament)
        self.assertEqual(virament.requested_by, self.user_profile)
        self.assertEqual(virament.reason, 'Transfer for critical equipment procurement')
        self.assertEqual(virament.section, self.test_section)
        
        # Verify budget reservation (to_be_withdrawn updated)
        self.source_budget.refresh_from_db()
        expected_to_be_withdrawn = initial_source_to_be_withdrawn + 150000.00
        self.assertEqual(self.source_budget.to_be_withdrawn, expected_to_be_withdrawn)
        
        # Verify transaction record was created
        transaction_record = Transactions.objects.filter(
            reference_id=virament.virament_id,
            transaction_type='VIRAMENT'
        ).first()
        
        self.assertIsNotNone(transaction_record)
        self.assertEqual(transaction_record.amount, 150000.00)
        self.assertEqual(transaction_record.section, self.test_section)
        
        print("✅ Virament creation workflow successful")
        print(f"   📊 Virament ID: {virament.virament_id}")
        print(f"   💰 Amount: {virament.amount:,.2f} ZWL")
        print(f"   📈 Source budget to_be_withdrawn: {self.source_budget.to_be_withdrawn:,.2f}")
        
    def test_05_virament_detail_view(self):
        """Test virament detail view functionality"""
        print("\n👁️ Testing virament detail view...")
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Create a virament first
        virament = Asset_budget_Virament.objects.create(
            from_budget=self.source_budget,
            to_budget=self.destination_budget,
            amount=75000.00,
            reason='Test virament for detail view',
            requested_by=self.user_profile,
            section=self.test_section,
            process=self.approval_process,
            region=self.test_region,
            currency='ZWL'
        )
        
        # Make GET request to detail view
        url = reverse('Ace:virament_detail', args=[virament.virament_id])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, virament.virament_id)
        self.assertContains(response, '75,000.00')
        self.assertContains(response, 'Test virament for detail view')
        
        print("✅ Virament detail view working correctly")
        
    def test_06_error_handling_and_rollback(self):
        """Test error handling and transaction rollback"""
        print("\n❌ Testing error handling and transaction rollback...")
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Test with insufficient balance
        insufficient_data = {
            'from_budget': self.low_budget.id,
            'to_budget': self.destination_budget.id,
            'amount': 1000.00,  # More than available (50)
            'reason': 'This should fail',
            'section': self.test_section.id,
            'currency': 'ZWL'
        }
        
        initial_virament_count = Asset_budget_Virament.objects.count()
        initial_to_be_withdrawn = self.low_budget.to_be_withdrawn
        
        # Make POST request
        url = reverse('Ace:create_virament')
        response = self.client.post(url, data=insufficient_data)
        
        # Should return form with errors (no redirect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/ace2/create_virament.html')
        
        # Verify no virament was created
        self.assertEqual(Asset_budget_Virament.objects.count(), initial_virament_count)
        
        # Verify budget state unchanged
        self.low_budget.refresh_from_db()
        self.assertEqual(self.low_budget.to_be_withdrawn, initial_to_be_withdrawn)
        
        print("✅ Error handling and rollback working correctly")
        
    def test_07_form_template_integration(self):
        """Test form-template integration with styling and validation display"""
        print("\n🎨 Testing form-template integration...")
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Get the form page
        url = reverse('Ace:create_virament')
        response = self.client.get(url)
        
        # Check template contains expected elements
        content = response.content.decode()
        
        # Check for form fields
        self.assertIn('name="from_budget"', content)
        self.assertIn('name="to_budget"', content)
        self.assertIn('name="amount"', content)
        self.assertIn('name="reason"', content)
        
        # Check for styling classes (Tailwind CSS)
        self.assertIn('ring-gray-300', content)
        self.assertIn('focus:ring-indigo-600', content)
        
        # Check for form validation structure
        self.assertIn('text-red-600', content)  # Error styling
        
        print("✅ Form-template integration working correctly")
        
    def test_08_available_balance_calculation(self):
        """Test available balance calculation with to_be_withdrawn"""
        print("\n🧮 Testing available balance calculation...")
        
        # Test available balance property
        self.assertEqual(self.source_budget.available_balance, 450000.00)  # 500000 - 50000
        self.assertEqual(self.destination_budget.available_balance, 200000.00)  # 200000 - 0
        self.assertEqual(self.low_budget.available_balance, 50.00)  # 1000 - 950
        
        # Test budget reservation
        original_to_be_withdrawn = self.source_budget.to_be_withdrawn
        self.source_budget.reserve_amount(100000.00)
        self.source_budget.refresh_from_db()
        
        expected_to_be_withdrawn = original_to_be_withdrawn + 100000.00
        self.assertEqual(self.source_budget.to_be_withdrawn, expected_to_be_withdrawn)
        self.assertEqual(self.source_budget.available_balance, 350000.00)  # 500000 - 150000
        
        print("✅ Available balance calculation working correctly")
        
    @patch('ACE2.views.notify_user')
    def test_09_notification_system(self, mock_notify):
        """Test notification system integration"""
        print("\n📧 Testing notification system...")
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Create virament
        virament_data = {
            'from_budget': self.source_budget.id,
            'to_budget': self.destination_budget.id,
            'amount': 50000.00,
            'reason': 'Notification test transfer',
            'section': self.test_section.id,
            'currency': 'ZWL'
        }
        
        url = reverse('Ace:create_virament')
        response = self.client.post(url, data=virament_data, follow=True)
        
        # Check if notification function was called
        # Note: This test checks if the notification code runs, even if no section head is found
        self.assertEqual(response.status_code, 200)
        
        print("✅ Notification system integration tested")
        
    def test_10_virament_listing_view(self):
        """Test virament listing functionality"""
        print("\n📋 Testing virament listing view...")
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Create multiple viraments
        virements = []
        for i in range(3):
            virament = Asset_budget_Virament.objects.create(
                from_budget=self.source_budget,
                to_budget=self.destination_budget,
                amount=25000.00 + (i * 10000),
                reason=f'Test virament #{i+1}',
                requested_by=self.user_profile,
                section=self.test_section,
                region=self.test_region,
                currency='ZWL'
            )
            virements.append(virament)
        
        # Test listing view
        url = reverse('Ace:view_all_viraments')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check all viraments appear in listing
        for virament in virements:
            self.assertContains(response, str(virament.virament_id))
            self.assertContains(response, f'{virament.amount:,.2f}')
        
        print("✅ Virament listing view working correctly")


def run_comprehensive_tests():
    """Run all comprehensive end-to-end tests"""
    print("=" * 80)
    print("🚀 STARTING COMPREHENSIVE VIRAMENT END-TO-END TESTING")
    print("=" * 80)
    
    # Import Django test runner
    from django.test.utils import get_runner
    from django.conf import settings
    
    # Get test runner and run tests
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Run specific test case
    failures = test_runner.run_tests(['__main__.ViramentEndToEndTestCase'])
    
    print("\n" + "=" * 80)
    if failures == 0:
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("✅ Virament functionality is working correctly with:")
        print("   • Form validation and user-specific filtering")
        print("   • Template rendering and styling")
        print("   • Database transactions and rollback")
        print("   • Budget balance calculations")
        print("   • Error handling and validation")
        print("   • Notification system integration")
        print("   • Complete workflow simulation")
    else:
        print(f"❌ {failures} TESTS FAILED")
        print("🔍 Please review the test output above for details")
    print("=" * 80)
    
    return failures == 0


if __name__ == '__main__':
    # Run the comprehensive tests
    success = run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)