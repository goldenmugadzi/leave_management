#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Asset_budget_Virament, AssetBudget, Transactions
from it.users.models import UserProfile

def detailed_investigation():
    print('=== DETAILED VIREMENT INVESTIGATION ===')
    
    # Get the specific virements
    virement_18 = Asset_budget_Virament.objects.get(virament_id=18)
    virement_17 = Asset_budget_Virament.objects.get(virament_id=17)
    
    virements = [virement_17, virement_18]
    
    for v in virements:
        print(f'\n{"="*80}')
        print(f'DETAILED ANALYSIS - VIREMENT {v.virament_id}')
        print(f'{"="*80}')
        
        print(f'Amount: {v.amount:,.2f} ZWG')
        print(f'Date: {v.date_created}')
        print(f'Purpose: {v.reason}')
        
        # Check if budgets were actually updated
        from_budget = v.from_budget
        to_budget = v.to_budget
        
        print(f'\nBUDGET IMPACT ANALYSIS:')
        print(f'From Budget: {from_budget.budget_name}')
        print(f'  Balance: {from_budget.balance:,.2f}')
        print(f'  Should have been reduced by: {v.amount:,.2f}')
        print(f'  Expected balance after virement: {from_budget.balance + v.amount:,.2f}')
        
        print(f'\nTo Budget: {to_budget.budget_name}')
        print(f'  Balance: {to_budget.balance:,.2f}')
        print(f'  Should have been increased by: {v.amount:,.2f}')
        print(f'  Expected balance before virement: {to_budget.balance - v.amount:,.2f}')
        
        # Check transaction status
        transaction = Transactions.objects.filter(virament_id=str(v.virament_id)).first()
        if transaction:
            print(f'\nTRANSACTION STATUS:')
            print(f'  Transaction ID: {transaction.transaction_id}')
            print(f'  Status: {transaction.approval_status}')
            print(f'  Expected final status: "approved by General Manager"')
            
            if transaction.approval_status != "approved by General Manager":
                print(f'  ⚠️  WARNING: Transaction not marked as fully approved!')
                print(f'     This may indicate the budget transfer was not executed.')
        
        # Check approval timestamps
        if v.process:
            approvals = v.process.approval_set.all()
            print(f'\nAPPROVAL TIMELINE:')
            for approval in approvals:
                print(f'  {approval.step.step}. {approval.step.to} - {approval.approved} by {approval.user.get_full_name()}')
                print(f'     Date: {approval.approved_at}')
        
        # Check for budget reservation vs actual transfer
        print(f'\nBUDGET RESERVATION CHECK:')
        print(f'  From Budget "to_be_withdrawn": {from_budget.to_be_withdrawn or 0:,.2f}')
        print(f'  Expected if not transferred: Should include {v.amount:,.2f}')
        print(f'  Expected if transferred: Should NOT include {v.amount:,.2f}')
        
        # Calculate expected vs actual
        if transaction and transaction.approval_status == "approved by General Manager":
            print(f'\n✅ EXPECTED: Budget transfer should be COMPLETED')
            print(f'   From budget should be reduced by {v.amount:,.2f}')
            print(f'   To budget should be increased by {v.amount:,.2f}')
        else:
            print(f'\n⚠️  EXPECTED: Budget transfer should be PENDING/RESERVED')
            print(f'   From budget should have {v.amount:,.2f} in "to_be_withdrawn"')
            print(f'   Actual budgets should be unchanged')

    # Check for discrepancies in the target budget
    target_budget = AssetBudget.objects.filter(budget_name__icontains='Regional Transmission West  Construction works').first()
    if target_budget:
        print(f'\n{"="*80}')
        print(f'TARGET BUDGET ANALYSIS: {target_budget.budget_name}')
        print(f'{"="*80}')
        
        # Calculate expected balance changes
        total_incoming = virement_17.amount + virement_18.amount  # 328,008,000 + 72,000,000
        print(f'Total incoming from both virements: {total_incoming:,.2f}')
        print(f'Current balance: {target_budget.balance:,.2f}')
        print(f'Current to_be_withdrawn: {target_budget.to_be_withdrawn:,.2f}')
        
        # Check all virements affecting this budget
        all_incoming = Asset_budget_Virament.objects.filter(to_budget=target_budget)
        all_outgoing = Asset_budget_Virament.objects.filter(from_budget=target_budget)
        
        print(f'\nALL VIREMENTS AFFECTING THIS BUDGET:')
        print(f'Incoming virements: {all_incoming.count()}')
        for v in all_incoming:
            status = "COMPLETED" if v.process and v.process.approval_set.count() == 3 else "PENDING"
            print(f'  + {v.amount:,.2f} from {v.from_budget.budget_name[:50]}... ({status})')
        
        print(f'Outgoing virements: {all_outgoing.count()}')
        for v in all_outgoing:
            status = "COMPLETED" if v.process and v.process.approval_set.count() == 3 else "PENDING"
            print(f'  - {v.amount:,.2f} to {v.to_budget.budget_name[:50]}... ({status})')

if __name__ == '__main__':
    try:
        detailed_investigation()
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()