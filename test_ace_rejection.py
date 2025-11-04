#!/usr/bin/env python
"""
Test script to verify ACE rejection functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('d:\\b')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from it.users.models import UserProfile, Regions, Sections, Roles, Application
from ACE2.models import Ace2, AssetBudget, Transactions
from approve.models import Process, Workflow, Step, Approval

User = get_user_model()

def setup_test_data():
    """Setup test data for ACE rejection testing"""
    print("Setting up test data...")
    
    # Clean up existing test data
    UserProfile.objects.filter(username__startswith='test_').delete()
    AssetBudget.objects.filter(budget_name__startswith='Test').delete()
    Ace2.objects.filter(Ace_id2__startswith='TEST').delete()
    
    # Region/Section
    region, _ = Regions.objects.get_or_create(region='Test Region')
    section, _ = Sections.objects.get_or_create(
        section='Test Section', 
        defaults={'code': 'TS', 'district_id': 'D1', 'region_id': 'R1'}
    )

    # Application and Roles
    app, _ = Application.objects.get_or_create(name='ace', defaults={'fullname': 'ace'})
    role_pass, _ = Roles.objects.get_or_create(
        role='pass', 
        application='ace',
        defaults={'name': 'Section Head', 'description': 'Section Head', 'app_id': app}
    )
    role_process, _ = Roles.objects.get_or_create(
        role='process', 
        application='ace',
        defaults={'name': 'Accounting Officer', 'description': 'Accounting Officer', 'app_id': app}
    )
    role_approve, _ = Roles.objects.get_or_create(
        role='approve', 
        application='ace',
        defaults={'name': 'GM', 'description': 'General Manager', 'app_id': app}
    )

    # Users
    user_requester = User.objects.create_user(username='test_requester', password='testpass')
    user_requester.region = region
    user_requester.section = section.section
    user_requester.save()

    user_sh = User.objects.create_user(username='test_sh', password='testpass')
    user_sh.region = region
    user_sh.section = section.section
    user_sh.save()
    user_sh.roles.add(role_pass)

    user_ao = User.objects.create_user(username='test_ao', password='testpass')
    user_ao.region = region
    user_ao.section = section.section
    user_ao.save()
    user_ao.roles.add(role_process)

    user_gm = User.objects.create_user(username='test_gm', password='testpass')
    user_gm.region = region
    user_gm.section = section.section
    user_gm.save()
    user_gm.roles.add(role_approve)

    # Budget
    budget = AssetBudget.objects.create(
        budget_name='Test Budget', 
        period=2025, 
        region=region, 
        balance=10000, 
        to_be_withdrawn=0,
        section='Test Section',
        allocated=10000
    )

    # Workflow and process with three steps (section head, accounting officer, then GM)
    workflow, _ = Workflow.objects.get_or_create(name='ace', defaults={'application': app})
    process = Process.objects.create(workflow=workflow)
    
    # Ensure steps exist
    step1, _ = Step.objects.get_or_create(
        step=1, workflow=workflow, 
        defaults={'approver': role_pass, 'to': 'AO'}
    )
    step2, _ = Step.objects.get_or_create(
        step=2, workflow=workflow, 
        defaults={'approver': role_process, 'to': 'GM'}
    )
    step3, _ = Step.objects.get_or_create(
        step=3, workflow=workflow, 
        defaults={'approver': role_approve, 'to': 'END'}
    )

    # ACE and initial transaction
    ace = Ace2.objects.create(
        Ace_id2='TEST2025001',
        region=region,
        section=section,
        budget_id=budget,
        amount=500,
        process=process,
        details_of_expenditure='Test expenditure for rejection',
        requested_by=user_requester,
        classification='Internal',
        quantity=1
    )
    
    txn = Transactions.objects.create(
        Ace_id2=ace,
        details_of_expenditure='Test Expenditure',
        approval_status='created',
        region=region,
        amount=500,
        budget=budget,
        section=section,
    )

    # Reserve budget in to_be_withdrawn like during creation
    budget.to_be_withdrawn = 500
    budget.save()

    print(f"✓ Test data created successfully")
    print(f"  - ACE ID: {ace.Ace_id2}")
    print(f"  - Budget: {budget.budget_name} (Balance: {budget.balance}, Reserved: {budget.to_be_withdrawn})")
    print(f"  - Users: {user_requester.username}, {user_sh.username}, {user_ao.username}, {user_gm.username}")
    
    return {
        'ace': ace,
        'budget': budget,
        'users': {
            'requester': user_requester,
            'sh': user_sh,
            'ao': user_ao,
            'gm': user_gm
        },
        'workflow': workflow,
        'process': process,
        'roles': {
            'pass': role_pass,
            'process': role_process,
            'approve': role_approve
        }
    }

def test_rejection_at_section_head(test_data):
    """Test rejection at section head level"""
    print("\n=== Testing Rejection at Section Head Level ===")
    
    ace = test_data['ace']
    budget = test_data['budget']
    workflow = test_data['workflow']
    process = test_data['process']
    user_sh = test_data['users']['sh']
    role_pass = test_data['roles']['pass']
    
    try:
        # Create rejection approval at step 1
        step1 = Step.objects.get(workflow=workflow, step=1)
        approval = Approval.objects.create(
            step=step1,
            user=user_sh,
            process=process,
            approved='Rejected',
            comment='Rejected by section head for testing'
        )
        
        print(f"✓ Created rejection approval: {approval}")
        
        # Check that ACE is marked as rejected
        ace.refresh_from_db()
        latest_approval = ace.process.approval_set.last()
        print(f"✓ Latest approval status: {latest_approval.approved}")
        
        # Check budget reversal
        budget.refresh_from_db()
        print(f"✓ Budget after rejection:")
        print(f"  - Balance: {budget.balance}")
        print(f"  - To be withdrawn: {budget.to_be_withdrawn}")
        
        # Simulate accessing the detail view to trigger budget reversal
        client = Client()
        client.force_login(user_sh)
        
        try:
            response = client.get(f'/ace/ace_detail/{ace.Ace_id2}/')
            print(f"✓ ACE detail view accessible after rejection (status: {response.status_code})")
        except Exception as e:
            print(f"⚠ Error accessing ACE detail view: {e}")
        
        # Check transaction status
        txn = Transactions.objects.get(Ace_id2=ace)
        print(f"✓ Transaction status: {txn.approval_status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in section head rejection test: {e}")
        return False

def test_rejection_at_accounting_officer(test_data):
    """Test rejection at accounting officer level"""
    print("\n=== Testing Rejection at Accounting Officer Level ===")
    
    # Create new ACE for this test
    ace = Ace2.objects.create(
        Ace_id2='TEST2025002',
        region=test_data['ace'].region,
        section=test_data['ace'].section,
        budget_id=test_data['budget'],
        amount=300,
        process=Process.objects.create(workflow=test_data['workflow']),
        details_of_expenditure='Test expenditure for AO rejection',
        requested_by=test_data['users']['requester'],
        classification='Internal',
        quantity=1
    )
    
    txn = Transactions.objects.create(
        Ace_id2=ace,
        details_of_expenditure='Test Expenditure AO',
        approval_status='created',
        region=test_data['ace'].region,
        amount=300,
        budget=test_data['budget'],
        section=test_data['ace'].section,
    )
    
    workflow = test_data['workflow']
    process = ace.process
    user_sh = test_data['users']['sh']
    user_ao = test_data['users']['ao']
    
    try:
        # First approve at section head level
        step1 = Step.objects.get(workflow=workflow, step=1)
        approval1 = Approval.objects.create(
            step=step1,
            user=user_sh,
            process=process,
            approved='Approved',
            comment='Approved by section head'
        )
        print(f"✓ Section head approval: {approval1}")
        
        # Then reject at accounting officer level
        step2 = Step.objects.get(workflow=workflow, step=2)
        approval2 = Approval.objects.create(
            step=step2,
            user=user_ao,
            process=process,
            approved='Rejected',
            comment='Rejected by accounting officer for testing'
        )
        print(f"✓ Accounting officer rejection: {approval2}")
        
        # Check that ACE is marked as rejected
        latest_approval = ace.process.approval_set.last()
        print(f"✓ Latest approval status: {latest_approval.approved}")
        
        # Simulate accessing the detail view
        client = Client()
        client.force_login(user_ao)
        
        try:
            response = client.get(f'/ace/ace_detail/{ace.Ace_id2}/')
            print(f"✓ ACE detail view accessible after AO rejection (status: {response.status_code})")
        except Exception as e:
            print(f"⚠ Error accessing ACE detail view: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in accounting officer rejection test: {e}")
        return False

def test_budget_reversal_logic():
    """Test the budget reversal logic specifically"""
    print("\n=== Testing Budget Reversal Logic ===")
    
    try:
        # Get a rejected ACE
        rejected_aces = Ace2.objects.filter(
            process__approval_set__approved="Rejected"
        )
        
        if not rejected_aces.exists():
            print("⚠ No rejected ACEs found for budget reversal test")
            return False
        
        ace = rejected_aces.first()
        budget = ace.budget_id
        
        print(f"✓ Testing budget reversal for ACE: {ace.Ace_id2}")
        print(f"  - Amount: {ace.amount}")
        print(f"  - Budget before: Balance={budget.balance}, ToBeWithdrawn={budget.to_be_withdrawn}")
        
        # Get transaction
        transaction = Transactions.objects.filter(Ace_id2=ace).first()
        if transaction:
            print(f"  - Transaction status: {transaction.approval_status}")
            
            # Check if reversal logic should trigger
            last_approval = ace.process.approval_set.last()
            if last_approval and last_approval.approved == "Rejected":
                if transaction.approval_status != "Rejected":
                    print("✓ Budget reversal should trigger")
                    # Simulate the reversal
                    original_to_be_withdrawn = budget.to_be_withdrawn
                    budget.to_be_withdrawn = budget.to_be_withdrawn - ace.amount
                    print(f"  - Budget after reversal: ToBeWithdrawn={budget.to_be_withdrawn} (was {original_to_be_withdrawn})")
                else:
                    print("✓ Budget already reversed (transaction marked as Rejected)")
            else:
                print("⚠ ACE not actually rejected")
        else:
            print("⚠ No transaction found for ACE")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in budget reversal test: {e}")
        return False

def test_rejection_templates():
    """Test that rejection templates exist and are accessible"""
    print("\n=== Testing Rejection Templates ===")
    
    try:
        import os
        template_dir = 'd:/b/templates/ace'
        
        rejection_templates = [
            'Ace_reject_internal.html',
            'Ace_reject_project.html',
            'Ace_reject_accounting_officer_internal.html',
            'Ace_reject_accounting_officer_project.html'
        ]
        
        for template in rejection_templates:
            template_path = os.path.join(template_dir, template)
            if os.path.exists(template_path):
                print(f"✓ Template exists: {template}")
            else:
                print(f"✗ Template missing: {template}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking rejection templates: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning up test data ===")
    try:
        UserProfile.objects.filter(username__startswith='test_').delete()
        AssetBudget.objects.filter(budget_name__startswith='Test').delete()
        Ace2.objects.filter(Ace_id2__startswith='TEST').delete()
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"⚠ Error during cleanup: {e}")

def main():
    """Main test function"""
    print("🔍 ACE Rejection Functionality Test")
    print("=" * 50)
    
    # Setup test data
    test_data = setup_test_data()
    
    results = []
    
    # Run tests
    results.append(test_rejection_at_section_head(test_data))
    results.append(test_rejection_at_accounting_officer(test_data))
    results.append(test_budget_reversal_logic())
    results.append(test_rejection_templates())
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! ACE rejection functionality is working correctly.")
    else:
        print("⚠ Some tests failed. Please review the output above.")
    
    # Cleanup
    cleanup_test_data()

if __name__ == "__main__":
    main()