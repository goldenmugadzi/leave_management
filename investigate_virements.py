#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Asset_budget_Virament, AssetBudget
from it.users.models import UserProfile

def investigate_virements():
    print('=== INVESTIGATING VIREMENTS ===')
    
    # Search for virements with the amounts mentioned
    target_amounts = [72000000.0, 328008000.0]
    virements = Asset_budget_Virament.objects.filter(amount__in=target_amounts).order_by('-date_created')
    
    print(f'Found {virements.count()} virements with target amounts')
    
    for v in virements:
        print('\n' + '='*60)
        print(f'VIREMENT ID: {v.virament_id}')
        print(f'Amount: {v.amount:,.2f} {v.currency or "ZWG"}')
        print(f'From Budget: {v.from_budget.budget_name if v.from_budget else "N/A"}')
        print(f'To Budget: {v.to_budget.budget_name if v.to_budget else "N/A"}')
        print(f'Requested By: {v.requested_by.get_full_name() if v.requested_by else "N/A"}')
        print(f'Date Created: {v.date_created}')
        print(f'Region: {v.region.region if v.region else "N/A"}')
        print(f'Section: {v.section.section if v.section else "N/A"}')
        print(f'Reason: {v.reason or "N/A"}')
        
        # Check budget impacts
        if v.from_budget:
            print(f'\nFROM BUDGET DETAILS:')
            print(f'  Current Balance: {v.from_budget.balance:,.2f}')
            print(f'  Allocated: {v.from_budget.allocated:,.2f}')
            print(f'  Withdrawn: {v.from_budget.withdrawn:,.2f}')
            print(f'  To be withdrawn: {v.from_budget.to_be_withdrawn:,.2f}' if v.from_budget.to_be_withdrawn else '  To be withdrawn: 0.00')
        
        if v.to_budget:
            print(f'\nTO BUDGET DETAILS:')
            print(f'  Current Balance: {v.to_budget.balance:,.2f}')
            print(f'  Allocated: {v.to_budget.allocated:,.2f}')
            print(f'  Withdrawn: {v.to_budget.withdrawn:,.2f}')
            print(f'  To be withdrawn: {v.to_budget.to_be_withdrawn:,.2f}' if v.to_budget.to_be_withdrawn else '  To be withdrawn: 0.00')
        
        # Check process status
        if v.process:
            approvals = v.process.approval_set.all()
            workflow_steps = v.process.workflow.step_set.count() if v.process.workflow else 0
            print(f'\nWORKFLOW PROCESS:')
            print(f'  Workflow: {v.process.workflow.name if v.process.workflow else "N/A"}')
            print(f'  Approvals: {approvals.count()}/{workflow_steps}')
            
            if approvals.exists():
                print('  APPROVAL HISTORY:')
                for approval in approvals:
                    print(f'    Step {approval.step.step}: {approval.approved} by {approval.user.get_full_name() if approval.user else "N/A"} on {approval.approved_at}')
            
            # Determine status
            if approvals.filter(approved='Rejected').exists():
                status = 'REJECTED'
            elif approvals.count() == workflow_steps and approvals.last().approved == 'Approved':
                status = 'FULLY APPROVED'
            elif approvals.exists():
                status = 'IN PROGRESS'
            else:
                status = 'PENDING'
            
            print(f'  STATUS: {status}')
        else:
            print('\nWORKFLOW PROCESS: No workflow process assigned')
        
        # Check for any related transactions
        from ACE2.models import Transactions
        transactions = Transactions.objects.filter(virament_id=str(v.virament_id))
        if transactions.exists():
            print(f'\nRELATED TRANSACTIONS: {transactions.count()}')
            for trans in transactions:
                print(f'  Transaction {trans.transaction_id}: {trans.approval_status}')
        else:
            print('\nRELATED TRANSACTIONS: None found')

    # Search for any virements containing "Sherwood" or "EPCC" in reason or related budgets
    print('\n\n' + '='*80)
    print('SEARCHING FOR SHERWOOD/EPCC RELATED VIREMENTS...')
    
    # Search in budget names
    sherwood_budgets = AssetBudget.objects.filter(budget_name__icontains='sherwood')
    epcc_budgets = AssetBudget.objects.filter(budget_name__icontains='epcc')
    
    related_virements = Asset_budget_Virament.objects.filter(
        models.Q(from_budget__in=sherwood_budgets) |
        models.Q(to_budget__in=sherwood_budgets) |
        models.Q(from_budget__in=epcc_budgets) |
        models.Q(to_budget__in=epcc_budgets) |
        models.Q(reason__icontains='sherwood') |
        models.Q(reason__icontains='epcc')
    ).distinct().order_by('-date_created')
    
    print(f'Found {related_virements.count()} Sherwood/EPCC related virements')
    
    for v in related_virements[:10]:  # Show first 10
        print(f'\nVirement {v.virament_id}: {v.amount:,.2f}')
        print(f'  From: {v.from_budget.budget_name if v.from_budget else "N/A"}')
        print(f'  To: {v.to_budget.budget_name if v.to_budget else "N/A"}')
        print(f'  Date: {v.date_created}')
        print(f'  Reason: {v.reason[:100] if v.reason else "N/A"}...')

if __name__ == '__main__':
    try:
        from django.db import models
        investigate_virements()
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()