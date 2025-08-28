#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Asset_budget_Virament, AssetBudget, Transactions
from approve.models import Approval

def check_virement_workflow_issue():
    print('=== CHECKING VIREMENT WORKFLOW ISSUE ===')
    
    # Get the specific virements
    virement_17 = Asset_budget_Virament.objects.get(virament_id=17)
    virement_18 = Asset_budget_Virament.objects.get(virament_id=18)
    
    for v in [virement_17, virement_18]:
        print(f'\n{"="*60}')
        print(f'VIREMENT {v.virament_id} WORKFLOW ANALYSIS')
        print(f'{"="*60}')
        
        if v.process:
            workflow = v.process.workflow
            all_steps = workflow.step_set.all().order_by('step')
            approvals = v.process.approval_set.all().order_by('step__step')
            
            print(f'Workflow: {workflow.name}')
            print(f'Total steps in workflow: {all_steps.count()}')
            print(f'Completed approvals: {approvals.count()}')
            
            print(f'\nWORKFLOW STEPS:')
            for step in all_steps:
                print(f'  Step {step.step}: {step.to} (Role: {step.approver.name})')
            
            print(f'\nCOMPLETED APPROVALS:')
            for approval in approvals:
                print(f'  Step {approval.step.step}: {approval.approved} by {approval.user.get_full_name()}')
                print(f'    Date: {approval.approved_at}')
                print(f'    Step Name: {approval.step.to}')
            
            # Check if all steps are completed
            is_fully_approved = approvals.count() == all_steps.count()
            last_approval_status = approvals.last().approved if approvals.exists() else None
            
            print(f'\nSTATUS ANALYSIS:')
            print(f'  All steps completed: {is_fully_approved}')
            print(f'  Last approval status: {last_approval_status}')
            print(f'  Should trigger budget update: {is_fully_approved and last_approval_status == "Approved"}')
            
            # Check transaction status
            transaction = Transactions.objects.filter(virament_id=str(v.virament_id)).first()
            if transaction:
                print(f'\nTRANSACTION DETAILS:')
                print(f'  ID: {transaction.transaction_id}')
                print(f'  Status: {transaction.approval_status}')
                print(f'  Amount: {transaction.amount}')
                print(f'  Date: {transaction.date_created}')
                
                # This should be "approved by General Manager" if fully processed
                if is_fully_approved and transaction.approval_status == "created":
                    print(f'  🚨 ISSUE FOUND: Transaction should be "approved by General Manager"')
                    print(f'     The virement approval logic may not be updating transaction status')
            
            # Check budget reservation
            from_budget = v.from_budget
            print(f'\nBUDGET RESERVATION STATUS:')
            print(f'  From budget to_be_withdrawn: {from_budget.to_be_withdrawn or 0:,.2f}')
            
            if is_fully_approved:
                # Should have been transferred and removed from to_be_withdrawn
                if (from_budget.to_be_withdrawn or 0) >= v.amount:
                    print(f'  🚨 ISSUE: Amount still reserved after full approval')
                    print(f'     Budget transfer may not have been executed')
                else:
                    print(f'  ✅ Good: Amount not in to_be_withdrawn (likely transferred)')
            else:
                # Should still be in to_be_withdrawn
                if (from_budget.to_be_withdrawn or 0) < v.amount:
                    print(f'  🚨 ISSUE: Amount not reserved but approval incomplete')
        
        # Check if there are any issues in the virement approval view
        print(f'\nRECOMMENDATION:')
        if is_fully_approved and transaction and transaction.approval_status == "created":
            print(f'  ⚠️  The virement appears fully approved but transaction status not updated')
            print(f'     This suggests the final approval step in virament_detail view may have failed')
            print(f'     or the approve_now logic was not triggered properly')
            print(f'     Manual intervention may be required to complete the budget transfer')

if __name__ == '__main__':
    try:
        check_virement_workflow_issue()
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()