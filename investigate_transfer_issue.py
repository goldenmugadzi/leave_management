#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Asset_budget_Virament, AssetBudget, Transactions
from it.users.models import UserProfile

def investigate_budget_transfer_issue():
    print('=== INVESTIGATING WHY BUDGET TRANSFERS DID NOT EXECUTE ===')
    
    # Get the specific virements
    virement_17 = Asset_budget_Virament.objects.get(virament_id=17)
    virement_18 = Asset_budget_Virament.objects.get(virament_id=18)
    
    # Check the user who made the final approval (Howard Choga)
    final_approver = UserProfile.objects.filter(first_name='Howard', last_name='Choga').first()
    if not final_approver:
        final_approver = UserProfile.objects.filter(username__icontains='howard').first()
    
    if final_approver:
        print(f'Final Approver: {final_approver.get_full_name()} ({final_approver.username})')
        
        # Check their virement role
        virement_roles = final_approver.roles.filter(application="virement")
        if virement_roles.exists():
            for role in virement_roles:
                print(f'  Virement role: {role.role}')
        else:
            print('  ❌ NO VIREMENT ROLE FOUND!')
            print('     This is likely why the budget transfer did not execute.')
            print('     The approve_now logic requires virement_role == "approve"')
    
    # Now check the actual budget histories to see if transfers occurred
    for v in [virement_17, virement_18]:
        print(f'\n{"="*60}')
        print(f'BUDGET TRANSFER VERIFICATION - VIREMENT {v.virament_id}')
        print(f'{"="*60}')
        
        from_budget = v.from_budget
        to_budget = v.to_budget
        amount = v.amount
        
        print(f'Transfer: {amount:,.2f} from "{from_budget.budget_name}" to "{to_budget.budget_name}"')
        
        # Current budget states
        print(f'\nCURRENT BUDGET STATES:')
        print(f'From Budget:')
        print(f'  Balance: {from_budget.balance:,.2f}')
        print(f'  Allocated: {from_budget.allocated:,.2f}')
        print(f'  Withdrawn: {from_budget.withdrawn:,.2f}')
        print(f'  To be withdrawn: {from_budget.to_be_withdrawn or 0:,.2f}')
        
        print(f'To Budget:')
        print(f'  Balance: {to_budget.balance:,.2f}')
        print(f'  Allocated: {to_budget.allocated:,.2f}')
        print(f'  Withdrawn: {to_budget.withdrawn:,.2f}')
        print(f'  To be withdrawn: {to_budget.to_be_withdrawn or 0:,.2f}')
        
        # Check if the transfer actually happened by looking at patterns
        # If transfer happened:
        # - From budget should be reduced by amount
        # - To budget should be increased by amount
        # - Transaction should be "approved by General Manager"
        
        transaction = Transactions.objects.filter(virament_id=str(v.virament_id)).first()
        transfer_executed = transaction and transaction.approval_status == "approved by General Manager"
        
        print(f'\nTRANSFER ANALYSIS:')
        print(f'  Transaction status: {transaction.approval_status if transaction else "N/A"}')
        print(f'  Transfer executed: {transfer_executed}')
        
        if not transfer_executed:
            print(f'  🚨 BUDGET TRANSFER NOT EXECUTED')
            print(f'     Despite full workflow approval, the actual budget transfer did not occur')
            print(f'     This means:')
            print(f'     - From budget still has full balance: {from_budget.balance:,.2f}')
            print(f'     - To budget did not receive the funds')
            print(f'     - Amount was not reserved in to_be_withdrawn')
        else:
            print(f'  ✅ Budget transfer executed successfully')
        
        # Look for issues in the virament approval logic
        if v.process:
            approvals = v.process.approval_set.all()
            workflow_complete = approvals.count() == v.process.workflow.step_set.count()
            last_approval_approved = approvals.last().approved == "Approved" if approvals.exists() else False
            
            print(f'\nWORKFLOW STATUS:')
            print(f'  Workflow complete: {workflow_complete}')
            print(f'  Last approval approved: {last_approval_approved}')
            print(f'  Should trigger transfer: {workflow_complete and last_approval_approved}')
            
            if workflow_complete and last_approval_approved and not transfer_executed:
                print(f'  🚨 CRITICAL ISSUE: Workflow complete but transfer not executed!')
                print(f'     Possible causes:')
                print(f'     1. Final approver lacks "approve" virement role')
                print(f'     2. Error occurred during budget update transaction')
                print(f'     3. approve_now condition was not met in virament_detail view')

    print(f'\n{"="*80}')
    print('SUMMARY OF INVESTIGATION')
    print(f'{"="*80}')
    print('Both virements show as fully approved in workflow but:')
    print('1. Transaction status remains "created" instead of "approved by General Manager"')
    print('2. This indicates the final budget transfer logic did not execute')
    print('3. Most likely cause: Final approver may not have "approve" virement role')
    print('4. The approve_now condition in virament_detail view requires:')
    print('   - User role = "approve" for virement application')
    print('   - All workflow steps completed')
    print('   - Last approval = "Approved"')
    print('\nRECOMMENDATION:')
    print('- Verify Howard Choga has "approve" role for virement application')
    print('- If role is missing, add it and re-visit virement detail pages')
    print('- Or manually execute budget transfers via Django admin/shell')

if __name__ == '__main__':
    try:
        investigate_budget_transfer_issue()
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()