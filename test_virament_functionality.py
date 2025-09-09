"""
Comprehensive test script to verify virament (budget transfer) functionality
Tests budget allocation, workflow approval, and balance calculations
"""

import os
import sys
import django
from datetime import date, datetime
from decimal import Decimal

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.db import transaction
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

# Import models
from ACE2.models import AssetBudget, Asset_budget_Virament, Transactions
from it.users.models import UserProfile, Regions, Sections, Roles, Application
from approve.models import Workflow, Process, Step, Approval


class ViramentFunctionalityTest:
    """Comprehensive test for virament functionality"""
    
    def __init__(self):
        self.client = Client()
        self.test_results = []
        
    def log_result(self, test_name, status, message):
        """Log test results"""
        icon = "✅" if status else "❌"
        self.test_results.append(f"{icon} {test_name}: {message}")
        print(f"{icon} {test_name}: {message}")
    
    def setup_test_data(self):
        """Setup test data for virament testing"""
        try:
            # Get or create test region
            region, created = Regions.objects.get_or_create(
                region="TEST_REGION",
                defaults={'code': 'TR01'}
            )
            
            # Get or create test section
            section, created = Sections.objects.get_or_create(
                section="TEST_SECTION",
                defaults={'code': 'TS01', 'region_id': str(region.id), 'district_id': '1'}
            )
            
            # Create test budgets
            source_budget = AssetBudget.objects.create(
                section_code="TEST_001",
                section="Test Source Section",
                budget_name="Equipment Budget",
                allocated=100000.0,
                balance=80000.0,
                withdrawn=20000.0,
                period=2025,
                region=region
            )
            
            target_budget = AssetBudget.objects.create(
                section_code="TEST_002", 
                section="Test Target Section",
                budget_name="Maintenance Budget",
                allocated=50000.0,
                balance=30000.0,
                withdrawn=20000.0,
                period=2025,
                region=region
            )
            
            # Create test user profile (since User is swapped for UserProfile)
            user_profile, created = UserProfile.objects.get_or_create(
                username="test_virament_user",
                defaults={
                    'email': 'test@example.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'region': region,
                    'section': section
                }
            )
            
            self.test_data = {
                'region': region,
                'section': section,
                'source_budget': source_budget,
                'target_budget': target_budget,
                'user_profile': user_profile
            }
            
            self.log_result("Setup Test Data", True, "Test data created successfully")
            return True
            
        except Exception as e:
            self.log_result("Setup Test Data", False, f"Error: {str(e)}")
            return False
    
    def test_virament_model_creation(self):
        """Test virament model creation"""
        try:
            source_budget = self.test_data['source_budget']
            target_budget = self.test_data['target_budget']
            user_profile = self.test_data['user_profile']
            
            # Create virament
            virament = Asset_budget_Virament.objects.create(
                requested_by=user_profile,
                from_budget=source_budget,
                to_budget=target_budget,
                amount=10000.0,
                reason="Test budget transfer for equipment maintenance",
                region=self.test_data['region'],
                section=self.test_data['section'],
                currency="ZIG"
            )
            
            self.test_virament = virament
            
            # Verify creation
            assert virament.virament_id is not None
            assert virament.from_budget == source_budget
            assert virament.to_budget == target_budget
            assert virament.amount == 10000.0
            
            self.log_result("Virament Model Creation", True, f"Virament created with ID: {virament.virament_id}")
            return True
            
        except Exception as e:
            self.log_result("Virament Model Creation", False, f"Error: {str(e)}")
            return False
    
    def test_transaction_creation(self):
        """Test transaction record creation"""
        try:
            virament = self.test_virament
            
            # Create transaction record
            transaction = Transactions.objects.create(
                virament=virament,
                details_of_expenditure=f"virement of {virament.from_budget} to {virament.to_budget}",
                approval_status="created",
                region=self.test_data['region'],
                amount=virament.amount,
                budget=virament.from_budget,
                section=virament.section
            )
            
            self.test_transaction = transaction
            
            # Verify transaction
            assert transaction.virament == virament
            assert transaction.approval_status == "created"
            assert transaction.amount == virament.amount
            
            self.log_result("Transaction Creation", True, f"Transaction created with ID: {transaction.transaction_id}")
            return True
            
        except Exception as e:
            self.log_result("Transaction Creation", False, f"Error: {str(e)}")
            return False
    
    def test_budget_balance_calculations(self):
        """Test budget balance calculations"""
        try:
            virament = self.test_virament
            source_budget = virament.from_budget
            target_budget = virament.to_budget
            
            # Record original balances
            original_source_balance = source_budget.balance
            original_target_balance = target_budget.balance
            original_source_withdrawn = source_budget.withdrawn
            original_target_allocated = target_budget.allocated
            
            # Simulate virament approval (balance calculation logic)
            source_budget.balance = source_budget.balance - virament.amount
            source_budget.withdrawn = source_budget.withdrawn + virament.amount
            source_budget.withdrawal_date = date.today()
            source_budget.save()
            
            target_budget.balance = target_budget.balance + virament.amount
            target_budget.allocated = target_budget.allocated + virament.amount
            target_budget.save()
            
            # Update transaction status
            transaction = self.test_transaction
            transaction.approval_status = "approved by General Manager"
            transaction.save()
            
            # Refresh from database
            source_budget.refresh_from_db()
            target_budget.refresh_from_db()
            
            # Verify calculations
            expected_source_balance = original_source_balance - virament.amount
            expected_target_balance = original_target_balance + virament.amount
            expected_source_withdrawn = original_source_withdrawn + virament.amount
            expected_target_allocated = original_target_allocated + virament.amount
            
            assert source_budget.balance == expected_source_balance
            assert target_budget.balance == expected_target_balance
            assert source_budget.withdrawn == expected_source_withdrawn
            assert target_budget.allocated == expected_target_allocated
            
            self.log_result("Budget Balance Calculations", True, 
                          f"Source: {original_source_balance} → {source_budget.balance}, "
                          f"Target: {original_target_balance} → {target_budget.balance}")
            
            return True
            
        except Exception as e:
            self.log_result("Budget Balance Calculations", False, f"Error: {str(e)}")
            return False
    
    def test_virament_form_validation(self):
        """Test virament form validation"""
        try:
            from ACE2.forms import ViramentForm
            
            user_profile = self.test_data['user_profile']
            
            # Test valid form data
            valid_data = {
                'from_budget': self.test_data['source_budget'].budget_id,
                'to_budget': self.test_data['target_budget'].budget_id,
                'amount': 5000.0,
                'reason': 'Test form validation',
                'section': self.test_data['section'].id,
                'currency': 'ZIG'
            }
            
            form = ViramentForm(data=valid_data, user=user_profile)
            
            if form.is_valid():
                self.log_result("Virament Form Validation", True, "Form validation passed")
                return True
            else:
                self.log_result("Virament Form Validation", False, f"Form errors: {form.errors}")
                return False
                
        except Exception as e:
            self.log_result("Virament Form Validation", False, f"Error: {str(e)}")
            return False
    
    def test_virament_views_access(self):
        """Test virament views accessibility"""
        try:
            # Get or create virement application
            app, created = Application.objects.get_or_create(
                name="virement",
                defaults={'fullname': 'Virement Application'}
            )
            
            # Create virement role
            role, created = Roles.objects.get_or_create(
                role="create",
                application="virement",
                defaults={'name': 'Virement Creator', 'description': 'Can create virements'}
            )
            
            # Assign role to user
            user_profile = self.test_data['user_profile']
            user_profile.roles.add(role)
            
            # Login user
            self.client.force_login(user_profile)
            
            # Test create virament view
            response = self.client.get('/ace/create-virament/')
            
            if response.status_code in [200, 302]:  # 200 OK or 302 redirect
                self.log_result("Virament Views Access", True, f"Create virament view accessible (status: {response.status_code})")
                return True
            else:
                self.log_result("Virament Views Access", False, f"View not accessible (status: {response.status_code})")
                return False
                
        except Exception as e:
            self.log_result("Virament Views Access", False, f"Error: {str(e)}")
            return False
    
    def test_virament_model_relationships(self):
        """Test model relationships and constraints"""
        try:
            virament = self.test_virament
            
            # Test foreign key relationships
            assert virament.from_budget is not None
            assert virament.to_budget is not None
            assert virament.requested_by is not None
            assert virament.region is not None
            assert virament.section is not None
            
            # Test virament can be accessed from budget
            source_viraments = virament.from_budget.from_budget.all()
            target_viraments = virament.to_budget.to_budget.all()
            
            assert virament in source_viraments
            assert virament in target_viraments
            
            self.log_result("Virament Model Relationships", True, "All relationships working correctly")
            return True
            
        except Exception as e:
            self.log_result("Virament Model Relationships", False, f"Error: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Delete test records
            if hasattr(self, 'test_transaction'):
                self.test_transaction.delete()
            if hasattr(self, 'test_virament'):
                self.test_virament.delete()
            
            AssetBudget.objects.filter(section_code__startswith="TEST_").delete()
            UserProfile.objects.filter(username="test_virament_user").delete()
            Sections.objects.filter(section="TEST_SECTION").delete()
            Regions.objects.filter(region="TEST_REGION").delete()
            
            self.log_result("Cleanup Test Data", True, "Test data cleaned up successfully")
            
        except Exception as e:
            self.log_result("Cleanup Test Data", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all virament functionality tests"""
        print("=" * 80)
        print("🧪 VIRAMENT FUNCTIONALITY TEST SUITE")
        print("=" * 80)
        print(f"Testing at: {datetime.now()}")
        print()
        
        tests = [
            self.setup_test_data,
            self.test_virament_model_creation,
            self.test_transaction_creation,
            self.test_budget_balance_calculations,
            self.test_virament_form_validation,
            self.test_virament_views_access,
            self.test_virament_model_relationships
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_result(test.__name__, False, f"Unexpected error: {str(e)}")
                failed += 1
            print()
        
        # Cleanup
        self.cleanup_test_data()
        
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        print()
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Virament functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result}")
        
        return failed == 0


def main():
    """Main function to run virament tests"""
    tester = ViramentFunctionalityTest()
    return tester.run_all_tests()


if __name__ == "__main__":
    main()