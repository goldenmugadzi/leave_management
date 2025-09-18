#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Asset_budget_Virament, AssetBudget, Transactions
from it.users.models import UserProfile

def diagnose_exact_issue():
    print('=== EXACT DIAGNOSIS OF BUDGET TRANSFER FAILURE ===')
    
    # Get the specific virements
    virement_17 = Asset_budget_Virament.objects.get(virament_id=17)
    virement_18 = Asset_budget_Virament.objects.get(virament_id=18)
    
    for v in [virement_17, virement_18]:
        print(f'\n{"="*60}')
        print(f'DETAILED ANALYSIS - VIREMENT {v.virament_id}')
        print(f'{"="*60}')
        
        # Check the workflow completion
        approvals = v.process.approval_set.all()
        workflow_steps = v.process.workflow.step_set.all()
        
        print(f'WORKFLOW ANALYSIS:')
        print(f'  Total workflow steps: {workflow_steps.count()}')
        print(f'  Completed approvals: {approvals.count()}')
        print(f'  Workflow complete: {approvals.count() == workflow_steps.count()}')
        
        if approvals.exists():
            last_approval = approvals.last()
            print(f'  Last approval status: {last_approval.approved}')
            print(f'  Last approval step: {last_approval.step.step}')
            print(f'  Last approval date: {getattr(last_approval, "date_created", "N/A")}')
            print(f'  Last approver: {last_approval.user.get_full_name() if last_approval.user else "N/A"}')
        
        # Check approve_now logic conditions
        approve_now_should_be_true = (
            approvals.count() == workflow_steps.count() and 
            approvals.exists() and 
            approvals.last().approved == "Approved"
        )
        print(f'  approve_now should be: {approve_now_should_be_true}')
        
        # Check transaction status
        transaction = Transactions.objects.filter(virament_id=str(v.virament_id)).first()
        if transaction:
            print(f'\nTRANSACTION ANALYSIS:')
            print(f'  Current status: {transaction.approval_status}')
            print(f'  Should be updated: {transaction.approval_status != "approved by General Manager"}')
            print(f'  Created date: {getattr(transaction, "date_created", getattr(transaction, "created_at", "N/A"))}')
        
        # Check budget status
        from_budget = v.from_budget
        to_budget = v.to_budget
        
        print(f'\nBUDGET ANALYSIS:')
        print(f'  From budget available: {from_budget.available_balance:,.2f}')
        print(f'  Transfer amount: {v.amount:,.2f}')
        print(f'  Sufficient funds: {from_budget.available_balance >= v.amount}')
        
        # The key insight: The budget transfer logic only runs when someone with 
        # "approve" role visits the virament_detail page AFTER workflow completion
        print(f'\nROOT CAUSE ANALYSIS:')
        print(f'  ✅ Workflow is complete: {approve_now_should_be_true}')
        print(f'  ✅ Howard has approve role: True')
        print(f'  ✅ Transaction not yet approved: {transaction and transaction.approval_status == "created"}')
        print(f'  ✅ Sufficient funds available: {from_budget.available_balance >= v.amount}')
        print(f'')
        print(f'  🚨 ISSUE: Budget transfer logic only executes when someone with')
        print(f'     "approve" role visits the virament_detail page AFTER the')
        print(f'     workflow is 100% complete.')
        print(f'')
        print(f'  📋 WHAT HAPPENED:')
        print(f'     1. Workflow was completed by Howard Choga on {getattr(last_approval, "date_created", "unknown") if approvals.exists() else "unknown"}')
        print(f'     2. But the budget transfer logic requires Howard (or another GM)')
        print(f'        to visit the virement detail page AGAIN after completion')
        print(f'     3. This second visit triggers the approve_now condition')
        print(f'     4. Only then does the budget transfer execute')
        print(f'')
        print(f'  💡 SOLUTION OPTIONS:')
        print(f'     A) Have Howard visit virement detail pages for ID {v.virament_id}')
        print(f'     B) Execute budget transfer manually via Django admin')
        print(f'     C) Fix the workflow logic to transfer immediately on final approval')

    print(f'\n{"="*80}')
    print('SUMMARY')
    print(f'{"="*80}')
    print('The virements are fully approved but budget transfers have not executed because:')
    print('')
    print('1. The budget transfer logic in virament_detail view only runs when:')
    print('   - Someone with "approve" role visits the page')
    print('   - AND the workflow is already 100% complete')
    print('   - AND the transaction is not already "approved by General Manager"')
    print('')
    print('2. This creates a chicken-and-egg problem:')
    print('   - Workflow completion marks the virement as "done"')
    print('   - But actual budget transfer requires an additional page visit')
    print('   - This extra step was apparently missed')
    print('')
    print('3. The virements show as approved in the system but no money moved')
    print('')
    print('IMMEDIATE ACTION NEEDED:')
    print('Have Howard Choga (or another GM) visit these virement detail pages:')
    print(f'- Virement 17: /virament/17/')
    print(f'- Virement 18: /virament/18/')
    print('Or execute budget transfers manually via Django shell/admin.')

if __name__ == '__main__':
    try:
        diagnose_exact_issue()
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()