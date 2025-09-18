#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Asset_budget_Virament, Transactions

def verify_virement_status():
    print('=== VERIFYING CURRENT VIREMENT STATUS ===')
    
    for virement_id in [17, 18]:
        print(f'\n{"="*60}')
        print(f'VIREMENT {virement_id} STATUS')
        print(f'{"="*60}')
        
        try:
            virement = Asset_budget_Virament.objects.get(virament_id=virement_id)
            transaction = Transactions.objects.filter(virament_id=str(virement_id)).first()
            
            print(f'Amount: {virement.amount:,.2f}')
            print(f'From Budget: {virement.from_budget.budget_name}')
            print(f'To Budget: {virement.to_budget.budget_name}')
            
            if transaction:
                print(f'Transaction Status: {transaction.approval_status}')
            else:
                print(f'❌ No transaction record found')
            
            # Check budget states
            from_budget = virement.from_budget
            to_budget = virement.to_budget
            
            print(f'\nFrom Budget State:')
            print(f'  Balance: {from_budget.balance:,.2f}')
            print(f'  Withdrawn: {from_budget.withdrawn:,.2f}')
            print(f'  To be withdrawn: {from_budget.to_be_withdrawn or 0:,.2f}')
            print(f'  Available: {from_budget.available_balance:,.2f}')
            
            print(f'To Budget State:')
            print(f'  Balance: {to_budget.balance:,.2f}')
            print(f'  Allocated: {to_budget.allocated:,.2f}')
            print(f'  Withdrawn: {to_budget.withdrawn:,.2f}')
            print(f'  To be withdrawn: {to_budget.to_be_withdrawn or 0:,.2f}')
            
            # Determine if transfer actually happened
            is_processed = transaction and transaction.approval_status == "approved by General Manager"
            print(f'\n🔍 ANALYSIS:')
            print(f'  Transaction shows as processed: {is_processed}')
            
            if is_processed:
                print(f'  ✅ Budget transfer completed successfully')
            else:
                print(f'  ❌ Budget transfer NOT completed - transaction status still "{transaction.approval_status if transaction else "N/A"}"')
                
        except Exception as e:
            print(f'❌ Error: {e}')

if __name__ == '__main__':
    verify_virement_status()