#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Asset_budget_Virament
from ACE2.utils import execute_virement_budget_transfer

def test_virement_budget_transfers():
    print('=== TESTING VIREMENT BUDGET TRANSFER FIX ===')
    
    # Test existing virements that should have been transferred but weren't
    virement_ids = [17, 18]
    
    for virement_id in virement_ids:
        print(f'\n{"="*60}')
        print(f'TESTING VIREMENT {virement_id}')
        print(f'{"="*60}')
        
        try:
            virement = Asset_budget_Virament.objects.get(virament_id=virement_id)
            
            print(f'Virement: {virement_id}')
            print(f'Amount: {virement.amount:,.2f}')
            print(f'From: {virement.from_budget.budget_name}')
            print(f'To: {virement.to_budget.budget_name}')
            
            # Check workflow completion
            if virement.process:
                approvals = virement.process.approval_set.all()
                workflow_steps = virement.process.workflow.step_set.all()
                workflow_complete = approvals.count() == workflow_steps.count()
                
                print(f'Workflow complete: {workflow_complete}')
                if workflow_complete and approvals.exists():
                    last_approval = approvals.last()
                    print(f'Last approval: {last_approval.approved}')
                    
                    if last_approval.approved == "Approved":
                        print(f'\n🔄 EXECUTING BUDGET TRANSFER...')
                        
                        # Execute the budget transfer using our new service function
                        result = execute_virement_budget_transfer(virement)
                        
                        if result['success']:
                            print(f'✅ SUCCESS: {result["message"]}')
                        else:
                            print(f'❌ FAILED: {result["error"]}')
                    else:
                        print(f'❌ Cannot transfer - last approval was not "Approved"')
                else:
                    print(f'❌ Cannot transfer - workflow not complete')
            else:
                print(f'❌ No workflow process found')
                
        except Asset_budget_Virament.DoesNotExist:
            print(f'❌ Virement {virement_id} not found')
        except Exception as e:
            print(f'❌ Error processing virement {virement_id}: {e}')
            import traceback
            traceback.print_exc()
    
    print(f'\n{"="*80}')
    print('TESTING COMPLETED')
    print('If transfers were successful, the virements should now show:')
    print('- Transaction status: "approved by General Manager"')
    print('- Budget balances updated correctly')
    print('- Funds actually transferred between budgets')
    print(f'{"="*80}')

if __name__ == '__main__':
    test_virement_budget_transfers()