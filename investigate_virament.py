#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the Python path
sys.path.append('d:\\b')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')  # Adjust if settings module name differs

django.setup()

from ACE2.models import Asset_budget_Virament, AssetBudget, Transactions

def investigate_virament():
    print("Recent Viraments:")
    viraments = Asset_budget_Virament.objects.all().order_by('-date_created')[:10]
    for v in viraments:
        print(f"ID: {v.virament_id}")
        print(f"  From Budget: {v.from_budget.budget_name if v.from_budget else 'None'}")
        print(f"  To Budget: {v.to_budget.budget_name if v.to_budget else 'None'}")
        print(f"  Amount: {v.amount}")
        print(f"  Currency: {v.currency}")
        print(f"  Date Created: {v.date_created}")
        print(f"  Process: {v.process.workflow.name if v.process and hasattr(v.process, 'workflow') and v.process.workflow else 'None'}")
        print(f"  Process Status: {v.process.status if v.process else 'None'}")
        
        # Check balances
        if v.from_budget:
            from_budget = AssetBudget.objects.get(budget_id=v.from_budget.budget_id)
            print(f"  From Budget Balance: {from_budget.balance}")
            print(f"  From Budget To Be Withdrawn: {from_budget.to_be_withdrawn}")
            print(f"  From Budget Available: {from_budget.available_balance}")
        
        if v.to_budget:
            to_budget = AssetBudget.objects.get(budget_id=v.to_budget.budget_id)
            print(f"  To Budget Balance: {to_budget.balance}")
            print(f"  To Budget To Be Withdrawn: {to_budget.to_be_withdrawn}")
            print(f"  To Budget Available: {to_budget.available_balance}")
        
        # Check transactions
        transactions = Transactions.objects.filter(virament=v)
        print(f"  Transactions Count: {transactions.count()}")
        for t in transactions:
            print(f"    Transaction ID: {t.transaction_id}, Amount: {t.amount}, Details: {t.details_of_expenditure}")
        
        print("-" * 50)

if __name__ == "__main__":
    investigate_virament()</content>
<parameter name="filePath">d:\b\investigate_virament.py