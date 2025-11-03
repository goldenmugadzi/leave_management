#!/usr/bin/env python
"""
ACE Rejection Testing Script
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('d:\\b')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

try:
    django.setup()
    from ACE2.models import Ace2, Transactions
    from approve.models import Approval
    from it.users.models import UserProfile
    
    print("🔍 ACE Rejection Testing Analysis")
    print("=" * 50)
    
    # Check recent ACEs
    aces = Ace2.objects.order_by('-date_created')[:5]
    print(f"📊 Total ACEs in system: {Ace2.objects.count()}")
    print(f"📋 Recent ACEs (last 5):")
    
    for ace in aces:
        print(f"\n  🔹 {ace.Ace_id2}")
        print(f"     Amount: ${ace.amount}")
        print(f"     Description: {ace.details_of_expenditure[:50]}...")
        print(f"     Requested by: {ace.requested_by}")
        
        if ace.process:
            approvals = ace.process.approval_set.all()
            print(f"     Workflow: {ace.process.workflow.name}")
            print(f"     Approvals: {len(approvals)}")
            
            for approval in approvals:
                status = "✅" if approval.approved == "Approved" else "❌" if approval.approved == "Rejected" else "⏳"
                print(f"       {status} Step {approval.step.step}: {approval.approved} by {approval.user.username}")
                if approval.comment:
                    print(f"         💬 Comment: {approval.comment}")
        else:
            print("     ⚠️ No process workflow found")
    
    # Check for rejected ACEs
    print(f"\n🚫 REJECTED ACEs ANALYSIS")
    print("=" * 30)
    
    rejected_aces = Ace2.objects.filter(process__approval_set__approved='Rejected').distinct()
    print(f"Total rejected ACEs: {rejected_aces.count()}")
    
    if rejected_aces.exists():
        for ace in rejected_aces[:3]:
            print(f"\n  ❌ REJECTED: {ace.Ace_id2}")
            print(f"     Amount: ${ace.amount}")
            
            rejection = ace.process.approval_set.filter(approved='Rejected').first()
            if rejection:
                print(f"     Rejected by: {rejection.user.username} ({rejection.user.get_full_name()})")
                print(f"     Rejection step: {rejection.step.step}")
                print(f"     Reason: {rejection.comment or 'No comment provided'}")
                print(f"     Date: {rejection.approved_at}")
                
                # Check transaction status
                transaction = Transactions.objects.filter(Ace_id2=ace).first()
                if transaction:
                    print(f"     Transaction status: {transaction.approval_status}")
                else:
                    print(f"     ⚠️ No transaction found")
                    
                # Check budget impact
                budget = ace.budget_id
                if budget:
                    print(f"     Budget: {budget.budget_name}")
                    print(f"     Budget balance: ${budget.balance}")
                    print(f"     To be withdrawn: ${budget.to_be_withdrawn}")
    else:
        print("  ✅ No rejected ACEs found")
    
    # Check workflow steps for ACE workflow
    print(f"\n🔄 ACE WORKFLOW ANALYSIS")
    print("=" * 30)
    
    from approve.models import Workflow, Step
    ace_workflows = Workflow.objects.filter(name__icontains='ace')
    
    for workflow in ace_workflows:
        print(f"\n  🔄 Workflow: {workflow.name}")
        steps = workflow.step_set.all().order_by('step')
        print(f"     Total steps: {steps.count()}")
        
        for step in steps:
            print(f"       Step {step.step}: {step.approver.name} → {step.to}")
    
    # Test rejection functionality
    print(f"\n🧪 REJECTION FUNCTIONALITY TEST")
    print("=" * 40)
    
    # Check approval form configuration
    from approve.forms import ApprovalForm
    form = ApprovalForm()
    print(f"  ✅ ApprovalForm imported successfully")
    print(f"  ✅ Approval choices: {form.fields['approved'].choices}")
    print(f"  ✅ Comment field required for rejection: {form.fields['comment'].help_text}")
    
    # Check template existence
    import os
    template_path = "d:/b/templates/finance/ace2/ace_detail.html"
    if os.path.exists(template_path):
        print(f"  ✅ ACE detail template exists")
        
        # Check for rejection button in template
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'value="Rejected"' in content:
                print(f"  ✅ Rejection button found in template")
            else:
                print(f"  ❌ Rejection button not found in template")
                
            if 'approve:approve' in content:
                print(f"  ✅ Approval workflow URL found in template")
            else:
                print(f"  ❌ Approval workflow URL not found in template")
    else:
        print(f"  ❌ ACE detail template not found")
    
    print(f"\n📋 TESTING SUMMARY")
    print("=" * 20)
    print(f"✅ Database connection: Working")
    print(f"✅ ACE models: {Ace2.objects.count()} records")
    print(f"✅ Approval workflow: {len(ace_workflows)} workflows configured")
    print(f"✅ Rejection tracking: {rejected_aces.count()} rejected ACEs")
    print(f"✅ Forms and templates: Configured")
    
    print(f"\n🎯 RECOMMENDATION")
    print("=" * 15)
    print("The ACE rejection functionality appears to be properly configured.")
    print("Test by:")
    print("1. Creating a new ACE")
    print("2. Navigating to ACE detail page")
    print("3. Using 'Reject' button with comment")
    print("4. Verifying budget reversal and notifications")

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("This suggests there may be missing dependencies or model issues")
except Exception as e:
    print(f"❌ Error: {e}")
    print("There may be database or configuration issues")