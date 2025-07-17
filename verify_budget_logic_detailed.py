#!/usr/bin/env python3
"""
Detailed Budget Logic Verification Script
=========================================

This script verifies the logic in ACE budget summary reports with special attention to:
1. Rejected ACEs and their budget impact
2. ACEs still in the approval tray (pending)
3. Budget field consistency (allocated, withdrawn, to_be_withdrawn, balance)

Key Issues to Check:
- Are rejected ACEs properly excluded from budget calculations?
- Are pending ACEs correctly reflected in to_be_withdrawn?
- Do budget fields add up correctly?
- Are there any orphaned transactions?
"""

import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal
from django.db.models import Sum, Q, Count
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import AssetBudget, Ace2, Transactions
from approve.models import Approval, Process
from it.users.models import Regions

class BudgetLogicVerifier:
    """Comprehensive budget logic verification"""
    
    def __init__(self):
        self.issues_found = []
        self.current_year = datetime.now().year
        self.regions = Regions.objects.all()
        
    def log_issue(self, level, message, details=None):
        """Log an issue with details"""
        issue = {
            'level': level,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now()
        }
        self.issues_found.append(issue)
        print(f"[{level}] {message}")
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")
        print()
    
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
    
    def verify_budget_consistency(self, budget):
        """Verify internal budget field consistency"""
        print(f"\n=== Verifying Budget: {budget.budget_name} ===")
        
        allocated = Decimal(str(budget.allocated or 0))
        withdrawn = Decimal(str(budget.withdrawn or 0))
        to_be_withdrawn = Decimal(str(budget.to_be_withdrawn or 0))
        balance = Decimal(str(budget.balance or 0))
        
        # Rule 1: allocated = withdrawn + to_be_withdrawn + balance
        calculated_allocated = withdrawn + to_be_withdrawn + balance
        if abs(allocated - calculated_allocated) > Decimal('0.01'):
            self.log_issue('ERROR', f'Budget allocation mismatch', {
                'budget_name': budget.budget_name,
                'allocated': allocated,
                'withdrawn': withdrawn,
                'to_be_withdrawn': to_be_withdrawn,
                'balance': balance,
                'calculated_allocated': calculated_allocated,
                'difference': allocated - calculated_allocated
            })
            return False
        
        # Rule 2: No negative values
        if withdrawn < 0 or to_be_withdrawn < 0 or balance < 0:
            self.log_issue('ERROR', f'Negative budget values detected', {
                'budget_name': budget.budget_name,
                'withdrawn': withdrawn,
                'to_be_withdrawn': to_be_withdrawn,
                'balance': balance
            })
            return False
        
        print(f"✓ Budget consistency check passed for {budget.budget_name}")
        return True
    
    def verify_ace_budget_impact(self, budget):
        """Verify ACE impact on budget calculations"""
        print(f"\n=== Verifying ACE Impact on Budget: {budget.budget_name} ===")
        
        # Get all ACEs for this budget
        aces = Ace2.objects.filter(budget_id=budget)
        
        # Categorize ACEs by approval status
        rejected_aces = []
        pending_aces = []
        approved_aces = []
        no_process_aces = []
        
        for ace in aces:
            status = self.get_ace_approval_status(ace)
            if status == 'REJECTED':
                rejected_aces.append(ace)
            elif status in ['PENDING', 'PARTIALLY_APPROVED']:
                pending_aces.append(ace)
            elif status == 'FULLY_APPROVED':
                approved_aces.append(ace)
            else:
                no_process_aces.append(ace)
        
        print(f"ACE Status Distribution:")
        print(f"  Rejected: {len(rejected_aces)}")
        print(f"  Pending/Partial: {len(pending_aces)}")
        print(f"  Fully Approved: {len(approved_aces)}")
        print(f"  No Process: {len(no_process_aces)}")
        
        # Calculate expected budget values
        expected_withdrawn = sum(Decimal(str(ace.amount or 0)) for ace in approved_aces)
        expected_to_be_withdrawn = sum(Decimal(str(ace.amount or 0)) for ace in pending_aces)
        
        actual_withdrawn = Decimal(str(budget.withdrawn or 0))
        actual_to_be_withdrawn = Decimal(str(budget.to_be_withdrawn or 0))
        
        # Check withdrawn amount
        if abs(expected_withdrawn - actual_withdrawn) > Decimal('0.01'):
            self.log_issue('ERROR', f'Withdrawn amount mismatch', {
                'budget_name': budget.budget_name,
                'expected_withdrawn': expected_withdrawn,
                'actual_withdrawn': actual_withdrawn,
                'difference': expected_withdrawn - actual_withdrawn,
                'approved_aces_count': len(approved_aces)
            })
        
        # Check to_be_withdrawn amount
        if abs(expected_to_be_withdrawn - actual_to_be_withdrawn) > Decimal('0.01'):
            self.log_issue('ERROR', f'To-be-withdrawn amount mismatch', {
                'budget_name': budget.budget_name,
                'expected_to_be_withdrawn': expected_to_be_withdrawn,
                'actual_to_be_withdrawn': actual_to_be_withdrawn,
                'difference': expected_to_be_withdrawn - actual_to_be_withdrawn,
                'pending_aces_count': len(pending_aces)
            })
        
        # Check for rejected ACEs still impacting budget
        if rejected_aces:
            rejected_amount = sum(Decimal(str(ace.amount or 0)) for ace in rejected_aces)
            print(f"\n⚠️  WARNING: {len(rejected_aces)} rejected ACEs totaling {rejected_amount}")
            print("These should NOT impact budget calculations:")
            for ace in rejected_aces[:5]:  # Show first 5
                print(f"  - {ace.Ace_id2}: {ace.amount} ({ace.details_of_expenditure[:50]}...)")
        
        # Verify transaction records
        self.verify_transaction_records(budget, aces)
        
        return True
    
    def verify_transaction_records(self, budget, aces):
        """Verify transaction records consistency"""
        print(f"\n--- Verifying Transaction Records ---")
        
        transaction_issues = []
        
        for ace in aces:
            transaction = Transactions.objects.filter(Ace_id2=ace).first()
            if not transaction:
                transaction_issues.append({
                    'ace_id': ace.Ace_id2,
                    'issue': 'Missing transaction record',
                    'amount': ace.amount
                })
                continue
            
            ace_status = self.get_ace_approval_status(ace)
            transaction_status = transaction.approval_status
            
            # Check consistency between ACE approval and transaction status
            if ace_status == 'REJECTED' and transaction_status != 'Rejected':
                transaction_issues.append({
                    'ace_id': ace.Ace_id2,
                    'issue': 'Rejected ACE but transaction not marked as rejected',
                    'ace_status': ace_status,
                    'transaction_status': transaction_status,
                    'amount': ace.amount
                })
            
            elif ace_status == 'FULLY_APPROVED' and transaction_status != 'approved by General Manager':
                transaction_issues.append({
                    'ace_id': ace.Ace_id2,
                    'issue': 'Approved ACE but transaction not marked as approved',
                    'ace_status': ace_status,
                    'transaction_status': transaction_status,
                    'amount': ace.amount
                })
        
        if transaction_issues:
            self.log_issue('ERROR', f'Transaction record inconsistencies found', {
                'budget_name': budget.budget_name,
                'issues_count': len(transaction_issues),
                'issues': transaction_issues[:10]  # Show first 10
            })
        else:
            print("✓ Transaction records are consistent")
    
    def verify_report_calculations(self, region=None):
        """Verify the calculations used in ace_reports view"""
        print(f"\n{'='*60}")
        print("VERIFYING ACE REPORT CALCULATIONS")
        print(f"{'='*60}")
        
        if region:
            budgets = AssetBudget.objects.filter(region=region, period=self.current_year)
            print(f"Checking budgets for region: {region.region}")
        else:
            budgets = AssetBudget.objects.filter(period=self.current_year)
            print(f"Checking all budgets for {self.current_year}")
        
        total_budget_issues = 0
        
        for budget in budgets:
            if budget.allocated and budget.allocated > 0:
                # Verify individual budget consistency
                if not self.verify_budget_consistency(budget):
                    total_budget_issues += 1
                
                # Verify ACE impact on budget
                self.verify_ace_budget_impact(budget)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: {total_budget_issues} budgets with issues out of {budgets.count()} total")
        print(f"{'='*60}")
    
    def check_orphaned_aces(self):
        """Check for ACEs without proper workflow or transaction records"""
        print(f"\n{'='*60}")
        print("CHECKING FOR ORPHANED ACEs")
        print(f"{'='*60}")
        
        # ACEs without process
        no_process_aces = Ace2.objects.filter(process__isnull=True)
        if no_process_aces.exists():
            self.log_issue('WARNING', f'ACEs without approval process', {
                'count': no_process_aces.count(),
                'examples': list(no_process_aces.values('Ace_id2', 'amount', 'details_of_expenditure')[:5])
            })
        
        # ACEs without transaction records
        ace_ids = Ace2.objects.values_list('Ace_id', flat=True)
        transaction_ace_ids = Transactions.objects.values_list('Ace_id2', flat=True)
        missing_transactions = set(ace_ids) - set(transaction_ace_ids)
        
        if missing_transactions:
            missing_aces = Ace2.objects.filter(Ace_id__in=missing_transactions)
            self.log_issue('WARNING', f'ACEs without transaction records', {
                'count': len(missing_transactions),
                'examples': list(missing_aces.values('Ace_id2', 'amount', 'details_of_expenditure')[:5])
            })
        
        # Transactions without ACEs
        orphaned_transactions = Transactions.objects.filter(Ace_id2__isnull=True)
        if orphaned_transactions.exists():
            self.log_issue('WARNING', f'Transactions without ACEs', {
                'count': orphaned_transactions.count(),
                'examples': list(orphaned_transactions.values('transaction_id', 'details_of_expenditure')[:5])
            })
    
    def analyze_budget_trends(self):
        """Analyze budget utilization trends"""
        print(f"\n{'='*60}")
        print("BUDGET UTILIZATION ANALYSIS")
        print(f"{'='*60}")
        
        budgets = AssetBudget.objects.filter(period=self.current_year, allocated__gt=0)
        
        high_utilization = []
        over_committed = []
        zero_utilization = []
        
        for budget in budgets:
            allocated = Decimal(str(budget.allocated or 0))
            withdrawn = Decimal(str(budget.withdrawn or 0))
            to_be_withdrawn = Decimal(str(budget.to_be_withdrawn or 0))
            
            utilization_rate = (withdrawn / allocated * 100) if allocated > 0 else 0
            commitment_rate = ((withdrawn + to_be_withdrawn) / allocated * 100) if allocated > 0 else 0
            
            if utilization_rate > 90:
                high_utilization.append({
                    'budget_name': budget.budget_name,
                    'utilization_rate': float(utilization_rate),
                    'allocated': float(allocated),
                    'withdrawn': float(withdrawn)
                })
            
            if commitment_rate > 100:
                over_committed.append({
                    'budget_name': budget.budget_name,
                    'commitment_rate': float(commitment_rate),
                    'allocated': float(allocated),
                    'committed': float(withdrawn + to_be_withdrawn)
                })
            
            if utilization_rate == 0:
                zero_utilization.append({
                    'budget_name': budget.budget_name,
                    'allocated': float(allocated)
                })
        
        if high_utilization:
            print(f"⚠️  HIGH UTILIZATION BUDGETS (>90%): {len(high_utilization)}")
            for budget in high_utilization[:5]:
                print(f"  - {budget['budget_name']}: {budget['utilization_rate']:.1f}% utilized")
        
        if over_committed:
            print(f"🚨 OVER-COMMITTED BUDGETS (>100%): {len(over_committed)}")
            for budget in over_committed[:5]:
                print(f"  - {budget['budget_name']}: {budget['commitment_rate']:.1f}% committed")
        
        if zero_utilization:
            print(f"📊 ZERO UTILIZATION BUDGETS: {len(zero_utilization)}")
    
    def generate_detailed_report(self):
        """Generate comprehensive report"""
        print(f"\n{'='*60}")
        print("DETAILED BUDGET LOGIC VERIFICATION REPORT")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Run all verification checks
        self.verify_report_calculations()
        self.check_orphaned_aces()
        self.analyze_budget_trends()
        
        # Summary
        print(f"\n{'='*60}")
        print("VERIFICATION SUMMARY")
        print(f"{'='*60}")
        
        error_count = len([issue for issue in self.issues_found if issue['level'] == 'ERROR'])
        warning_count = len([issue for issue in self.issues_found if issue['level'] == 'WARNING'])
        
        print(f"Total Issues Found: {len(self.issues_found)}")
        print(f"  - Errors: {error_count}")
        print(f"  - Warnings: {warning_count}")
        
        if error_count > 0:
            print(f"\n🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for issue in self.issues_found:
                if issue['level'] == 'ERROR':
                    print(f"  - {issue['message']}")
        
        if warning_count > 0:
            print(f"\n⚠️  WARNINGS FOR REVIEW:")
            for issue in self.issues_found:
                if issue['level'] == 'WARNING':
                    print(f"  - {issue['message']}")
        
        if error_count == 0 and warning_count == 0:
            print(f"\n✅ ALL BUDGET LOGIC CHECKS PASSED!")
        
        return self.issues_found

def main():
    """Run the budget logic verification"""
    print("Budget Logic Verification Tool")
    print("=" * 50)
    
    verifier = BudgetLogicVerifier()
    
    # Run specific region if needed
    # region = Regions.objects.first()
    # verifier.verify_report_calculations(region)
    
    # Run full verification
    issues = verifier.generate_detailed_report()
    
    # Save results to file
    with open('budget_logic_verification_results.txt', 'w') as f:
        f.write(f"Budget Logic Verification Results\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*50}\n\n")
        
        for issue in issues:
            f.write(f"[{issue['level']}] {issue['message']}\n")
            if issue['details']:
                for key, value in issue['details'].items():
                    f.write(f"  {key}: {value}\n")
            f.write(f"  Timestamp: {issue['timestamp']}\n\n")
    
    print(f"\nDetailed results saved to: budget_logic_verification_results.txt")

if __name__ == "__main__":
    main()
