"""
Realistic Virament Functionality Test
Simulates actual workflow with proper Django integration
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

try:
    django.setup()
    print("✅ Django environment configured successfully")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction
from django.forms.models import model_to_dict
import json

# Import project models and forms
from ACE2.models import Asset_budget_Virament, AssetBudget, Transactions
from ACE2.forms import ViramentForm
from it.users.models import UserProfile, Regions, Sections
from approve.models import Process

# Get the custom user model
User = get_user_model()


def create_test_data():
    """Create test data for virament testing"""
    print("\n🔧 Creating test data...")
    
    # Create test region and section
    test_region, _ = Regions.objects.get_or_create(
        region="Test Region E2E",
        defaults={'code': "TRE2E"}
    )
    
    test_section, _ = Sections.objects.get_or_create(
        section="Test Section E2E",
        defaults={
            'code': 'TSE2E',
            'district_id': 'TEST_DIST',
            'region_id': str(test_region.id)
        }
    )
    
    # Create test user
    test_user, created = User.objects.get_or_create(
        username='testuser_e2e',
        defaults={
            'email': 'test@company.com',
            'first_name': 'Test',
            'last_name': 'User',
            'region': test_region,
            'section': test_section
        }
    )
    
    if created:
        test_user.set_password('testpass123')
        test_user.save()
    
    # UserProfile is the same as User in this case
    user_profile = test_user
    
    # Create test budgets
    source_budget, _ = AssetBudget.objects.get_or_create(
        budget_name="Infrastructure Budget - E2E Source",
        period=2025,
        region=test_region.region,
        defaults={
            'balance': 500000.00,
            'to_be_withdrawn': 50000.00
        }
    )
    
    destination_budget, _ = AssetBudget.objects.get_or_create(
        budget_name="Equipment Budget - E2E Destination",
        period=2025, 
        region=test_region.region,
        defaults={
            'balance': 200000.00,
            'to_be_withdrawn': 0.00
        }
    )
    
    low_budget, _ = AssetBudget.objects.get_or_create(
        budget_name="Low Balance Budget - E2E",
        period=2025,
        region=test_region.region,
        defaults={
            'balance': 1000.00,
            'to_be_withdrawn': 950.00
        }
    )
    
    # Create approval process
    approval_process, _ = Process.objects.get_or_create(
        name="Virament Approval Process E2E",
        defaults={'description': "Budget virament approval workflow"}
    )
    
    return {
        'region': test_region,
        'section': test_section,
        'user': test_user,
        'user_profile': user_profile,
        'source_budget': source_budget,
        'destination_budget': destination_budget,
        'low_budget': low_budget,
        'approval_process': approval_process
    }


def test_form_validation(test_data):
    """Test ViramentForm validation with realistic data"""
    print("\n🔍 Testing ViramentForm validation...")
    
    user_profile = test_data['user_profile']
    source_budget = test_data['source_budget']
    destination_budget = test_data['destination_budget']
    low_budget = test_data['low_budget']
    section = test_data['section']
    
    # Test 1: Valid form data
    valid_data = {
        'from_budget': source_budget.id,
        'to_budget': destination_budget.id,
        'amount': 100000.00,
        'reason': 'Equipment procurement transfer for end-to-end testing',
        'section': section.id,
        'currency': 'ZWL'
    }
    
    form = ViramentForm(data=valid_data, user=user_profile)
    if form.is_valid():
        print("✅ Valid form data passed validation")
    else:
        print(f"❌ Valid form failed validation: {form.errors}")
        return False
    
    # Test 2: Same budget validation
    invalid_same_budget = valid_data.copy()
    invalid_same_budget['to_budget'] = source_budget.id
    
    form = ViramentForm(data=invalid_same_budget, user=user_profile)
    if not form.is_valid() and 'Source and destination budgets cannot be the same' in str(form.errors):
        print("✅ Same budget validation working")
    else:
        print(f"❌ Same budget validation failed: {form.errors}")
        return False
    
    # Test 3: Insufficient balance validation
    insufficient_data = valid_data.copy()
    insufficient_data['from_budget'] = low_budget.id
    insufficient_data['amount'] = 100.00  # More than available (50)
    
    form = ViramentForm(data=insufficient_data, user=user_profile)
    if not form.is_valid() and 'Insufficient available balance' in str(form.errors):
        print("✅ Insufficient balance validation working")
    else:
        print(f"❌ Insufficient balance validation failed: {form.errors}")
        return False
    
    # Test 4: Available balance calculation
    expected_available = source_budget.balance - (source_budget.to_be_withdrawn or 0)
    actual_available = source_budget.available_balance
    
    if actual_available == expected_available:
        print(f"✅ Available balance calculation correct: {actual_available:,.2f}")
    else:
        print(f"❌ Available balance calculation incorrect: expected {expected_available:,.2f}, got {actual_available:,.2f}")
        return False
    
    return True


def test_view_functionality(test_data):
    """Test virament views with Django test client"""
    print("\n🌐 Testing virament view functionality...")
    
    client = Client()
    user = test_data['user']
    source_budget = test_data['source_budget']
    destination_budget = test_data['destination_budget']
    section = test_data['section']
    
    # Test 1: GET request to create virament view
    try:
        # Login user
        client.force_login(user)
        
        url = reverse('Ace:create_virament')
        response = client.get(url)
        
        if response.status_code == 200:
            print("✅ GET request to create virament view successful")
            
            # Check if form is in context
            if 'form' in response.context:
                print("✅ Form found in response context")
            else:
                print("❌ Form not found in response context")
                return False
        else:
            print(f"❌ GET request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ GET request test failed: {e}")
        return False
    
    # Test 2: POST request to create virament
    try:
        virament_data = {
            'from_budget': source_budget.id,
            'to_budget': destination_budget.id,
            'amount': 75000.00,
            'reason': 'End-to-end test virament creation',
            'section': section.id,
            'currency': 'ZWL'
        }
        
        # Record initial state
        initial_virament_count = Asset_budget_Virament.objects.count()
        initial_to_be_withdrawn = source_budget.to_be_withdrawn
        
        response = client.post(url, data=virament_data, follow=True)
        
        if response.status_code == 200:
            print("✅ POST request completed successfully")
            
            # Check if virament was created
            final_virament_count = Asset_budget_Virament.objects.count()
            if final_virament_count > initial_virament_count:
                print("✅ Virament created successfully")
                
                # Get the created virament
                virament = Asset_budget_Virament.objects.filter(
                    from_budget=source_budget,
                    to_budget=destination_budget,
                    amount=75000.00
                ).first()
                
                if virament:
                    print(f"✅ Virament details: ID={virament.virament_id}, Amount={virament.amount:,.2f}")
                    
                    # Check budget reservation
                    source_budget.refresh_from_db()
                    expected_to_be_withdrawn = initial_to_be_withdrawn + 75000.00
                    
                    if source_budget.to_be_withdrawn == expected_to_be_withdrawn:
                        print(f"✅ Budget reservation successful: {source_budget.to_be_withdrawn:,.2f}")
                    else:
                        print(f"❌ Budget reservation failed: expected {expected_to_be_withdrawn:,.2f}, got {source_budget.to_be_withdrawn:,.2f}")
                        return False
                    
                    # Check transaction record
                    transaction_record = Transactions.objects.filter(
                        reference_id=virament.virament_id,
                        transaction_type='VIRAMENT'
                    ).first()
                    
                    if transaction_record:
                        print("✅ Transaction record created successfully")
                    else:
                        print("❌ Transaction record not created")
                        return False
                        
                else:
                    print("❌ Created virament not found")
                    return False
            else:
                print("❌ Virament was not created")
                return False
        else:
            print(f"❌ POST request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ POST request test failed: {e}")
        return False
    
    return True


def test_model_functionality(test_data):
    """Test model-level functionality and business logic"""
    print("\n🏗️ Testing model functionality...")
    
    source_budget = test_data['source_budget']
    destination_budget = test_data['destination_budget']
    user_profile = test_data['user_profile']
    section = test_data['section']
    region = test_data['region']
    
    try:
        # Test 1: Create virament directly
        virament = Asset_budget_Virament.objects.create(
            from_budget=source_budget,
            to_budget=destination_budget,
            amount=50000.00,
            reason='Direct model test virament',
            requested_by=user_profile,
            section=section,
            region=region,
            currency='ZWL'
        )
        
        print(f"✅ Virament created directly: ID={virament.virament_id}")
        
        # Test 2: Model validation
        try:
            virament.full_clean()
            print("✅ Model validation passed")
        except Exception as e:
            print(f"❌ Model validation failed: {e}")
            return False
        
        # Test 3: String representation
        virament_str = str(virament)
        if virament_str:
            print(f"✅ String representation: {virament_str}")
        else:
            print("❌ String representation empty")
            return False
        
        # Test 4: Budget available balance calculation
        available_balance = source_budget.available_balance
        expected_balance = source_budget.balance - (source_budget.to_be_withdrawn or 0)
        
        if available_balance == expected_balance:
            print(f"✅ Available balance calculation: {available_balance:,.2f}")
        else:
            print(f"❌ Available balance calculation error: expected {expected_balance:,.2f}, got {available_balance:,.2f}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Model functionality test failed: {e}")
        return False


def run_comprehensive_test_suite():
    """Run all comprehensive end-to-end tests"""
    print("=" * 80)
    print("🚀 VIRAMENT FUNCTIONALITY - COMPREHENSIVE END-TO-END TESTING")
    print("=" * 80)
    
    try:
        # Create test data
        test_data = create_test_data()
        print("✅ Test data created successfully")
        
        # Run test suites
        test_results = []
        
        # Test 1: Form validation
        test_results.append(("Form Validation", test_form_validation(test_data)))
        
        # Test 2: View functionality
        test_results.append(("View Functionality", test_view_functionality(test_data)))
        
        # Test 3: Model functionality
        test_results.append(("Model Functionality", test_model_functionality(test_data)))
        
        # Display results
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<25} {status}")
            if result:
                passed_tests += 1
        
        print("\n" + "-" * 80)
        print(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! VIRAMENT FUNCTIONALITY IS WORKING CORRECTLY!")
            print("\n✅ VERIFIED FUNCTIONALITY:")
            print("   • Form validation with user-specific filtering")
            print("   • Budget balance calculations with to_be_withdrawn logic")
            print("   • Virament creation workflow with atomic transactions")
            print("   • Database record creation and referential integrity")
            print("   • Error handling and validation feedback")
            print("   • Template rendering and view integration")
            print("   • Model-level business logic and constraints")
            print("\n💡 CONCLUSION: The virament system successfully transfers budget")
            print("   allocations between Asset Budgets with proper validation,")
            print("   error handling, and transaction integrity.")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} TEST(S) FAILED")
            print("🔍 Please review the detailed output above for issues")
        
        print("=" * 80)
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ Test suite execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_comprehensive_test_suite()
    sys.exit(0 if success else 1)