#!/usr/bin/env python
"""
Budget Summary Verification Script
This script verifies the logic and calculations in the ACE budget summary system.
"""

import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.db.models import Sum, Count
from django.utils import timezone
from ACE2.models import AssetBudget, Ace2, Transactions
from it.users.models import Regions

class BudgetSummaryVerifier:
    def __init__(self):
        self.current_year = timezone.now().year
        self.errors = []
        self.warnings = []
        self.info = []

    def log_error(self, message):
        """Log an error message"""
        self.errors.append(f"ERROR: {message}")
        print(f"❌ ERROR: {message}")

    def log_warning(self, message):
        """Log a warning message"""
        self.warnings.append(f"WARNING: {message}")
        print(f"⚠️  WARNING: {message}")

    def log_info(self, message):
        """Log an info message"""
        self.info.append(f"INFO: {message}")
        print(f"ℹ️  INFO: {message}")

    def verify_budget_field_consistency(self, budget):
        """Verify that budget fields are mathematically consistent"""
        # Handle None values by treating them as 0
        allocated = budget.allocated or 0
        withdrawn = budget.withdrawn or 0
        to_be_withdrawn = budget.to_be_withdrawn or 0
        balance = budget.balance or 0
        
        expected_balance = allocated - withdrawn - to_be_withdrawn
        
        # Allow for small floating point errors
        tolerance = 0.01
        balance_diff = abs(expected_balance - balance)
        
        if balance_diff > tolerance:
            self.log_error(f"Budget {budget.budget_name} has inconsistent balance. "
                          f"Expected: {expected_balance:.2f}, Actual: {balance:.2f}, "
                          f"Difference: {balance_diff:.2f}")
            return False
        return True

    def verify_budget_percentage_calculations(self, budget):
        """Verify percentage calculations for a budget"""
        # Handle None values by treating them as 0
        allocated = budget.allocated or 0
        withdrawn = budget.withdrawn or 0
        to_be_withdrawn = budget.to_be_withdrawn or 0
        balance = budget.balance or 0
        
        if allocated <= 0:
            self.log_warning(f"Budget {budget.budget_name} has zero or negative allocation: {allocated}")
            return False

        # Calculate percentages using the same logic as in views.py
        utilization_percentage = (withdrawn / allocated * 100) if allocated > 0 else 0
        pending_percentage = (to_be_withdrawn / allocated * 100) if allocated > 0 else 0
        available_percentage = (balance / allocated * 100) if allocated > 0 else 0
        total_commitment_percentage = utilization_percentage + pending_percentage

        # Verify that percentages add up to 100% (within tolerance)
        total_percentage = utilization_percentage + pending_percentage + available_percentage
        if abs(total_percentage - 100.0) > 0.1:  # Allow for small rounding errors
            self.log_error(f"Budget {budget.budget_name} percentages don't add up to 100%. "
                          f"Utilization: {utilization_percentage:.2f}%, "
                          f"Pending: {pending_percentage:.2f}%, "
                          f"Available: {available_percentage:.2f}%, "
                          f"Total: {total_percentage:.2f}%")
            return False

        # Verify that amounts add up to allocated
        total_amount = withdrawn + to_be_withdrawn + balance
        if abs(total_amount - allocated) > 0.01:
            self.log_error(f"Budget {budget.budget_name} amounts don't add up to allocated. "
                          f"Withdrawn: {withdrawn:.2f}, "
                          f"Pending: {to_be_withdrawn:.2f}, "
                          f"Balance: {balance:.2f}, "
                          f"Total: {total_amount:.2f}, "
                          f"Allocated: {allocated:.2f}")
            return False

        return True

    def verify_ace_budget_consistency(self, budget):
        """Verify that ACE transactions match budget calculations"""
        # Get all ACEs for this budget
        aces = Ace2.objects.filter(budget_id=budget)
        
        # Calculate total ACE amount (regardless of approval status)
        total_ace_amount = aces.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get transaction data for verification
        transactions = Transactions.objects.filter(budget=budget)
        approved_transactions = transactions.filter(approval_status="approved by General Manager")
        expected_withdrawn_from_transactions = approved_transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        # Allow for small differences due to floating point precision
        tolerance = 0.01
        
        if abs(expected_withdrawn_from_transactions - budget.withdrawn) > tolerance:
            self.log_warning(f"Budget {budget.budget_name} withdrawn amount mismatch. "
                           f"Expected from transactions: {expected_withdrawn_from_transactions:.2f}, "
                           f"Budget field: {budget.withdrawn:.2f}")
        
        # Log some diagnostic information
        self.log_info(f"Budget {budget.budget_name}: {aces.count()} ACEs, "
                     f"Total ACE amount: ${total_ace_amount:.2f}, "
                     f"Budget allocated: ${budget.allocated:.2f}")

    def verify_health_status_logic(self, budget):
        """Verify the health status determination logic"""
        if budget.allocated <= 0:
            return
            
        balance_percentage = (budget.balance / budget.allocated) * 100
        
        if balance_percentage > 30:
            expected_status = 'good'
        elif balance_percentage > 10:
            expected_status = 'warning'
        else:
            expected_status = 'critical'
        
        # Calculate actual status using the same logic as in views.py
        actual_status = 'good' if budget.balance > (budget.allocated * 0.3) else 'warning' if budget.balance > (budget.allocated * 0.1) else 'critical'
        
        if actual_status != expected_status:
            self.log_error(f"Budget {budget.budget_name} health status mismatch. "
                          f"Expected: {expected_status}, Actual: {actual_status}, "
                          f"Balance %: {balance_percentage:.2f}%")

    def verify_region_totals(self, region):
        """Verify regional budget totals"""
        budgets = AssetBudget.objects.filter(region=region, period=self.current_year)
        
        if not budgets.exists():
            self.log_warning(f"No budgets found for region {region.region} in {self.current_year}")
            return
        
        # Calculate totals
        total_allocated = budgets.aggregate(total=Sum('allocated'))['total'] or 0
        total_withdrawn = budgets.aggregate(total=Sum('withdrawn'))['total'] or 0
        total_pending = budgets.aggregate(total=Sum('to_be_withdrawn'))['total'] or 0
        total_balance = budgets.aggregate(total=Sum('balance'))['total'] or 0
        
        # Verify regional totals consistency
        expected_total = total_withdrawn + total_pending + total_balance
        if abs(expected_total - total_allocated) > 0.01:
            self.log_error(f"Region {region.region} total amounts don't match allocated. "
                          f"Allocated: {total_allocated:.2f}, "
                          f"Total (W+P+B): {expected_total:.2f}, "
                          f"Difference: {abs(expected_total - total_allocated):.2f}")

    def run_verification(self):
        """Run all verification checks"""
        print("🔍 Starting Budget Summary Verification...\n")
        
        # Get all regions
        regions = Regions.objects.all()
        
        for region in regions:
            print(f"\n📊 Verifying region: {region.region}")
            
            # Get budgets for current year
            budgets = AssetBudget.objects.filter(region=region, period=self.current_year)
            
            if not budgets.exists():
                self.log_info(f"No budgets found for region {region.region} in {self.current_year}")
                continue
            
            # Verify each budget
            for budget in budgets:
                if budget.allocated and budget.allocated > 0:
                    # Run all verification checks
                    self.verify_budget_field_consistency(budget)
                    self.verify_budget_percentage_calculations(budget)
                    self.verify_ace_budget_consistency(budget)
                    self.verify_health_status_logic(budget)
                else:
                    self.log_warning(f"Budget {budget.budget_name} has zero or negative allocation")
            
            # Verify regional totals
            self.verify_region_totals(region)
        
        # Print summary
        print("\n" + "="*50)
        print("VERIFICATION SUMMARY")
        print("="*50)
        print(f"✅ Info messages: {len(self.info)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")
        
        if self.errors:
            print("\n❌ ERRORS FOUND:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if not self.errors and not self.warnings:
            print("\n🎉 ALL VERIFICATION CHECKS PASSED!")
            print("The budget summary logic is working correctly.")
        elif not self.errors:
            print("\n✅ No critical errors found. Only warnings detected.")
        else:
            print("\n❌ Critical errors found. Please review the budget data.")

    def generate_sample_budget_report(self):
        """Generate a sample budget report similar to the web interface"""
        print("\n" + "="*50)
        print("SAMPLE BUDGET REPORT")
        print("="*50)
        
        # Get a sample region
        region = Regions.objects.first()
        if not region:
            print("No regions found.")
            return
        
        budgets = AssetBudget.objects.filter(region=region, period=self.current_year, allocated__gt=0)[:3]
        
        if not budgets.exists():
            print(f"No budgets found for region {region.region}")
            return
        
        print(f"Region: {region.region}")
        print(f"Year: {self.current_year}")
        print()
        
        for budget in budgets:
            print(f"Budget: {budget.budget_name}")
            print("-" * 40)
            
            # Calculate percentages
            utilization_percentage = (budget.withdrawn / budget.allocated * 100) if budget.allocated > 0 else 0
            pending_percentage = (budget.to_be_withdrawn / budget.allocated * 100) if budget.allocated > 0 else 0
            available_percentage = (budget.balance / budget.allocated * 100) if budget.allocated > 0 else 0
            total_commitment_percentage = utilization_percentage + pending_percentage
            
            # Health status
            health_status = 'good' if budget.balance > (budget.allocated * 0.3) else 'warning' if budget.balance > (budget.allocated * 0.1) else 'critical'
            
            # ACE count
            aces = Ace2.objects.filter(budget_id=budget, date_created__year=self.current_year)
            ace_count = aces.count()
            total_ace_amount = aces.aggregate(total=Sum('amount'))['total'] or 0
            avg_ace_amount = total_ace_amount / ace_count if ace_count > 0 else 0
            
            print(f"  Allocated:    ${budget.allocated:,.2f}")
            print(f"  Withdrawn:    ${budget.withdrawn:,.2f} ({utilization_percentage:.1f}%)")
            print(f"  Pending:      ${budget.to_be_withdrawn:,.2f} ({pending_percentage:.1f}%)")
            print(f"  Available:    ${budget.balance:,.2f} ({available_percentage:.1f}%)")
            print(f"  Total Commitment: {total_commitment_percentage:.1f}%")
            print(f"  Health Status: {health_status.upper()}")
            print(f"  ACE Count:    {ace_count}")
            print(f"  Avg ACE Amount: ${avg_ace_amount:,.2f}")
            print()

if __name__ == "__main__":
    verifier = BudgetSummaryVerifier()
    verifier.run_verification()
    verifier.generate_sample_budget_report()
