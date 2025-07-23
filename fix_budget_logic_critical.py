#!/usr/bin/env python3
"""
Critical Budget Logic Fix Script
===============================

This script addresses the most critical issues found in the budget logic verification:
1. Updates transaction records for rejected ACEs
2. Recalculates budget fields based on actual ACE approval statuses
3. Fixes budget allocation mismatches

IMPORTANT: This script should be run during maintenance hours as it will modify budget data.
"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import AssetBudget, Ace2, Transactions
from approve.models import Approval, Process

class BudgetLogicFixer:
    """Fix critical budget logic issues"""
    
    def __init__(self):
        self.fixes_applied = []
        self.errors_encountered = []
        
    def log_fix(self, description, details=None):
        """Log a fix that was applied"""
        fix_info = {
            'description': description,
            'details': details or {},
            'timestamp': datetime.now()
        }
        self.fixes_applied.append(fix_info)
        print(f"✓ {description}")
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")
    
    def log_error(self, description, details=None):
        """Log an error encountered"""
        error_info = {
            'description': description,
            'details': details or {},
            'timestamp': datetime.now()
        }
        self.errors_encountered.append(error_info)
        print(f"✗ ERROR: {description}")
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")
    
    def get_ace_approval_status(self, ace):
        """Get the current approval status of an ACE"""
        if not ace.process:
            return 'NO_PROCESS'
        
        approvals = ace.process.approval_set.all().order_by('-approved_at')
        if not approvals.exists():
            return 'PENDING'
        
        last_approval = approvals.first()
        if last_approval.approved == 'Rejected':
            return 'REJECTED'
        elif last_approval.approved == 'Approved':
            # Check if this is the final approval
            total_steps = ace.process.workflow.step_set.count()
            completed_approvals = approvals.filter(approved='Approved').count()
            if completed_approvals >= total_steps:
                return 'FULLY_APPROVED'
            else:
                return 'PARTIALLY_APPROVED'
        else:
            return 'PENDING'
    
    def fix_transaction_records(self):
        """Fix transaction records for rejected ACEs"""
        print("\n=== FIXING TRANSACTION RECORDS ===")
        
        fixed_count = 0
        
        # Get all ACEs with processes
        aces = Ace2.objects.filter(process__isnull=False)
        
        for ace in aces:
            ace_status = self.get_ace_approval_status(ace)
            transaction = Transactions.objects.filter(Ace_id2=ace).first()
            
            if not transaction:
                continue
            
            # Fix rejected ACEs with incorrect transaction status
            if ace_status == 'REJECTED' and transaction.approval_status != 'Rejected':
                old_status = transaction.approval_status
                transaction.approval_status = 'Rejected'
                transaction.save()
                
                fixed_count += 1
                self.log_fix(f"Updated transaction record for rejected ACE", {
                    'ace_id': ace.Ace_id2,
                    'old_status': old_status,
                    'new_status': 'Rejected',
                    'amount': ace.amount
                })
            
            # Fix approved ACEs with incorrect transaction status
            elif ace_status == 'FULLY_APPROVED' and transaction.approval_status != 'approved by General Manager':
                old_status = transaction.approval_status
                transaction.approval_status = 'approved by General Manager'
                transaction.save()
                
                fixed_count += 1
                self.log_fix(f"Updated transaction record for approved ACE", {
                    'ace_id': ace.Ace_id2,
                    'old_status': old_status,
                    'new_status': 'approved by General Manager',
                    'amount': ace.amount
                })
        
        print(f"\\nFixed {fixed_count} transaction records")
        return fixed_count
    
    def recalculate_budget_fields(self):
        """Recalculate budget fields based on actual ACE statuses"""
        print("\\n=== RECALCULATING BUDGET FIELDS ===")
        
        fixed_budgets = 0
        
        # Get all budgets with ACEs
        budgets = AssetBudget.objects.filter(ace2__isnull=False).distinct()
        
        for budget in budgets:
            aces = Ace2.objects.filter(budget_id=budget)
            
            # Categorize ACEs by status
            approved_amount = Decimal('0')
            pending_amount = Decimal('0')
            
            for ace in aces:
                if not ace.amount:
                    continue
                
                ace_status = self.get_ace_approval_status(ace)
                amount = Decimal(str(ace.amount))
                
                if ace_status == 'FULLY_APPROVED':
                    approved_amount += amount
                elif ace_status in ['PENDING', 'PARTIALLY_APPROVED']:
                    pending_amount += amount
                # Rejected ACEs don't contribute to any amount
            
            # Calculate what the budget fields should be
            allocated = Decimal(str(budget.allocated or 0))
            old_withdrawn = Decimal(str(budget.withdrawn or 0))
            old_to_be_withdrawn = Decimal(str(budget.to_be_withdrawn or 0))
            old_balance = Decimal(str(budget.balance or 0))
            
            # New values
            new_withdrawn = approved_amount
            new_to_be_withdrawn = pending_amount
            new_balance = allocated - new_withdrawn - new_to_be_withdrawn
            
            # Check if updates are needed
            if (abs(old_withdrawn - new_withdrawn) > Decimal('0.01') or
                abs(old_to_be_withdrawn - new_to_be_withdrawn) > Decimal('0.01') or
                abs(old_balance - new_balance) > Decimal('0.01')):
                
                # Update budget fields
                budget.withdrawn = float(new_withdrawn)
                budget.to_be_withdrawn = float(new_to_be_withdrawn)
                budget.balance = float(new_balance)
                budget.save()
                
                fixed_budgets += 1
                self.log_fix(f"Recalculated budget fields", {
                    'budget_name': budget.budget_name,
                    'old_withdrawn': float(old_withdrawn),
                    'new_withdrawn': float(new_withdrawn),
                    'old_to_be_withdrawn': float(old_to_be_withdrawn),
                    'new_to_be_withdrawn': float(new_to_be_withdrawn),
                    'old_balance': float(old_balance),
                    'new_balance': float(new_balance)
                })
        
        print(f"\\nFixed {fixed_budgets} budget records")
        return fixed_budgets
    
    def validate_budget_consistency(self):
        """Validate that budget fields are now consistent"""
        print("\\n=== VALIDATING BUDGET CONSISTENCY ===")
        
        consistent_budgets = 0
        inconsistent_budgets = 0
        
        budgets = AssetBudget.objects.filter(allocated__gt=0)
        
        for budget in budgets:
            allocated = Decimal(str(budget.allocated or 0))
            withdrawn = Decimal(str(budget.withdrawn or 0))
            to_be_withdrawn = Decimal(str(budget.to_be_withdrawn or 0))
            balance = Decimal(str(budget.balance or 0))
            
            calculated_total = withdrawn + to_be_withdrawn + balance
            
            if abs(allocated - calculated_total) > Decimal('0.01'):
                inconsistent_budgets += 1
                self.log_error(f"Budget still inconsistent after fix", {
                    'budget_name': budget.budget_name,
                    'allocated': float(allocated),
                    'calculated_total': float(calculated_total),
                    'difference': float(allocated - calculated_total)
                })
            else:
                consistent_budgets += 1
        
        print(f"\\nValidation Results:")
        print(f"  Consistent budgets: {consistent_budgets}")
        print(f"  Inconsistent budgets: {inconsistent_budgets}")
        
        return inconsistent_budgets == 0
    
    def generate_fix_report(self):
        """Generate a report of all fixes applied"""
        print("\\n=== GENERATING FIX REPORT ===")
        
        report_content = []
        report_content.append("Budget Logic Fix Report")
        report_content.append("=" * 50)
        report_content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_content.append(f"Fixes Applied: {len(self.fixes_applied)}")
        report_content.append(f"Errors Encountered: {len(self.errors_encountered)}")
        report_content.append("")
        
        if self.fixes_applied:
            report_content.append("FIXES APPLIED:")
            report_content.append("-" * 30)
            for fix in self.fixes_applied:
                report_content.append(f"- {fix['description']}")
                if fix['details']:
                    for key, value in fix['details'].items():
                        report_content.append(f"  {key}: {value}")
                report_content.append("")
        
        if self.errors_encountered:
            report_content.append("ERRORS ENCOUNTERED:")
            report_content.append("-" * 30)
            for error in self.errors_encountered:
                report_content.append(f"- {error['description']}")
                if error['details']:
                    for key, value in error['details'].items():
                        report_content.append(f"  {key}: {value}")
                report_content.append("")
        
        # Save report
        with open('budget_logic_fix_report.txt', 'w') as f:
            f.write("\\n".join(report_content))
        
        print(f"Fix report saved to: budget_logic_fix_report.txt")
    
    def run_all_fixes(self):
        """Run all fixes in sequence"""
        print("BUDGET LOGIC FIX SCRIPT")
        print("=" * 50)
        print("This script will fix critical budget logic issues.")
        print("Please ensure you have a database backup before proceeding.")
        
        response = input("\\nProceed with fixes? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
        
        try:
            with transaction.atomic():
                # Fix 1: Update transaction records
                self.fix_transaction_records()
                
                # Fix 2: Recalculate budget fields
                self.recalculate_budget_fields()
                
                # Fix 3: Validate results
                is_consistent = self.validate_budget_consistency()
                
                if is_consistent:
                    print("\\n✅ ALL FIXES APPLIED SUCCESSFULLY!")
                    print("Budget logic is now consistent.")
                else:
                    print("\\n⚠️  SOME INCONSISTENCIES REMAIN")
                    print("Please review the error log for details.")
                
        except Exception as e:
            print(f"\\n❌ ERROR DURING FIX APPLICATION: {e}")
            self.log_error("Critical error during fix application", {'error': str(e)})
            print("All changes have been rolled back.")
            
        finally:
            # Generate report
            self.generate_fix_report()

def main():
    """Main function"""
    fixer = BudgetLogicFixer()
    fixer.run_all_fixes()

if __name__ == "__main__":
    main()
