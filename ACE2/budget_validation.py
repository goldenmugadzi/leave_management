"""
Budget Validation Service for ACE System
Provides validation and integrity checks for budget operations
"""

from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from typing import Dict, List, Optional, Tuple
import logging

from .models import AssetBudget, Ace2, Transactions, Asset_budget_Virament


logger = logging.getLogger(__name__)


class BudgetValidationError(Exception):
    """Custom exception for budget validation errors"""
    pass


class BudgetIntegrityService:
    """Service for validating and maintaining budget data integrity"""
    
    @staticmethod
    def validate_budget_consistency(budget: AssetBudget) -> Dict[str, any]:
        """
        Validate that budget fields are mathematically consistent
        
        Args:
            budget: AssetBudget instance to validate
            
        Returns:
            Dict containing validation results and any errors
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'calculations': {}
        }
        
        try:
            # Handle None values by treating them as 0
            allocated = Decimal(str(budget.allocated or 0))
            withdrawn = Decimal(str(budget.withdrawn or 0))
            to_be_withdrawn = Decimal(str(budget.to_be_withdrawn or 0))
            balance = Decimal(str(budget.balance or 0))
            
            # Store calculations for reference
            result['calculations'] = {
                'allocated': float(allocated),
                'withdrawn': float(withdrawn),
                'to_be_withdrawn': float(to_be_withdrawn),
                'balance': float(balance)
            }
            
            # Check if allocated is positive
            if allocated <= 0:
                result['warnings'].append(f"Budget has zero or negative allocation: {allocated}")
                return result
            
            # Calculate expected balance
            expected_balance = allocated - withdrawn - to_be_withdrawn
            result['calculations']['expected_balance'] = float(expected_balance)
            
            # Check balance consistency (allow small floating point errors)
            balance_diff = abs(expected_balance - balance)
            if balance_diff > Decimal('0.01'):
                result['is_valid'] = False
                result['errors'].append(
                    f"Budget balance inconsistency. Expected: {expected_balance}, "
                    f"Actual: {balance}, Difference: {balance_diff}"
                )
            
            # Check that percentages add up to 100%
            utilization_pct = (withdrawn / allocated * 100) if allocated > 0 else 0
            pending_pct = (to_be_withdrawn / allocated * 100) if allocated > 0 else 0
            available_pct = (balance / allocated * 100) if allocated > 0 else 0
            
            result['calculations']['utilization_percentage'] = float(utilization_pct)
            result['calculations']['pending_percentage'] = float(pending_pct)
            result['calculations']['available_percentage'] = float(available_pct)
            
            total_percentage = utilization_pct + pending_pct + available_pct
            if abs(total_percentage - 100) > Decimal('0.1'):
                result['is_valid'] = False
                result['errors'].append(
                    f"Percentages don't add up to 100%. "
                    f"Utilization: {utilization_pct:.2f}%, "
                    f"Pending: {pending_pct:.2f}%, "
                    f"Available: {available_pct:.2f}%, "
                    f"Total: {total_percentage:.2f}%"
                )
                
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"Validation error: {str(e)}")
            logger.error(f"Budget validation error for {budget.budget_name}: {str(e)}")
        
        return result
    
    @staticmethod
    def validate_ace_against_budget(ace_amount: Decimal, budget: AssetBudget) -> Dict[str, any]:
        """
        Validate that an ACE can be created against a budget
        
        Args:
            ace_amount: Amount of the ACE to validate
            budget: Budget to validate against
            
        Returns:
            Dict containing validation results
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'impact': {}
        }
        
        try:
            # First validate budget consistency
            budget_validation = BudgetIntegrityService.validate_budget_consistency(budget)
            if not budget_validation['is_valid']:
                result['is_valid'] = False
                result['errors'].extend(budget_validation['errors'])
                return result
            
            # Handle None values
            allocated = Decimal(str(budget.allocated or 0))
            withdrawn = Decimal(str(budget.withdrawn or 0))
            to_be_withdrawn = Decimal(str(budget.to_be_withdrawn or 0))
            balance = Decimal(str(budget.balance or 0))
            ace_amount = Decimal(str(ace_amount))
            
            # Calculate impact
            new_to_be_withdrawn = to_be_withdrawn + ace_amount
            new_balance = balance - ace_amount
            
            result['impact'] = {
                'current_balance': float(balance),
                'ace_amount': float(ace_amount),
                'new_balance': float(new_balance),
                'new_to_be_withdrawn': float(new_to_be_withdrawn),
                'utilization_after_approval': float((withdrawn + ace_amount) / allocated * 100) if allocated > 0 else 0
            }
            
            # Check if ACE amount is positive
            if ace_amount <= 0:
                result['is_valid'] = False
                result['errors'].append("ACE amount must be positive")
                return result
            
            # Check if there's sufficient balance
            if new_balance < 0:
                result['is_valid'] = False
                result['errors'].append(
                    f"Insufficient budget balance. Required: {ace_amount}, "
                    f"Available: {balance}, Shortfall: {abs(new_balance)}"
                )
            
            # Check if total commitment doesn't exceed allocation
            total_commitment = withdrawn + new_to_be_withdrawn
            if total_commitment > allocated:
                result['is_valid'] = False
                result['errors'].append(
                    f"Total commitment would exceed allocation. "
                    f"Allocated: {allocated}, Total commitment: {total_commitment}"
                )
            
            # Warning if balance gets low
            if new_balance < (allocated * Decimal('0.1')):
                result['warnings'].append(
                    f"Budget balance will be critically low after this ACE: {new_balance}"
                )
            elif new_balance < (allocated * Decimal('0.3')):
                result['warnings'].append(
                    f"Budget balance will be low after this ACE: {new_balance}"
                )
                
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"Validation error: {str(e)}")
            logger.error(f"ACE validation error: {str(e)}")
        
        return result
    
    @staticmethod
    def get_budget_health_status(budget: AssetBudget) -> Dict[str, any]:
        """
        Get comprehensive health status for a budget
        
        Args:
            budget: Budget to analyze
            
        Returns:
            Dict containing health status and metrics
        """
        try:
            allocated = Decimal(str(budget.allocated or 0))
            balance = Decimal(str(budget.balance or 0))
            
            if allocated <= 0:
                return {
                    'status': 'inactive',
                    'message': 'Budget has no allocation',
                    'color': 'gray'
                }
            
            balance_percentage = (balance / allocated * 100) if allocated > 0 else 0
            
            if balance_percentage > 30:
                status = 'good'
                color = 'green'
                message = f'Budget is healthy with {balance_percentage:.1f}% available'
            elif balance_percentage > 10:
                status = 'warning'
                color = 'yellow'
                message = f'Budget requires monitoring with {balance_percentage:.1f}% available'
            else:
                status = 'critical'
                color = 'red'
                message = f'Budget is critically low with {balance_percentage:.1f}% available'
            
            return {
                'status': status,
                'message': message,
                'color': color,
                'balance_percentage': float(balance_percentage)
            }
            
        except Exception as e:
            logger.error(f"Budget health check error: {str(e)}")
            return {
                'status': 'error',
                'message': f'Health check failed: {str(e)}',
                'color': 'red'
            }
    
    @staticmethod
    def calculate_accurate_budget_summary(budget: AssetBudget) -> Dict[str, any]:
        """
        Calculate accurate budget summary with proper validation
        
        Args:
            budget: Budget to summarize
            
        Returns:
            Dict containing accurate budget summary
        """
        try:
            # Validate budget first
            validation = BudgetIntegrityService.validate_budget_consistency(budget)
            
            # Get ACE statistics
            current_year = timezone.now().year
            budget_aces = Ace2.objects.filter(
                budget_id=budget,
                date_created__year=current_year
            )
            
            ace_count = budget_aces.count()
            total_ace_amount = budget_aces.aggregate(total=Sum('amount'))['total'] or 0
            avg_ace_amount = total_ace_amount / ace_count if ace_count > 0 else 0
            
            # Get health status
            health = BudgetIntegrityService.get_budget_health_status(budget)
            
            # Handle None values
            allocated = Decimal(str(budget.allocated or 0))
            withdrawn = Decimal(str(budget.withdrawn or 0))
            to_be_withdrawn = Decimal(str(budget.to_be_withdrawn or 0))
            balance = Decimal(str(budget.balance or 0))
            
            # Calculate percentages
            utilization_percentage = (withdrawn / allocated * 100) if allocated > 0 else 0
            pending_percentage = (to_be_withdrawn / allocated * 100) if allocated > 0 else 0
            available_percentage = (balance / allocated * 100) if allocated > 0 else 0
            total_commitment_percentage = utilization_percentage + pending_percentage
            
            return {
                'budget': budget,
                'allocated': float(allocated),
                'withdrawn': float(withdrawn),
                'to_be_withdrawn': float(to_be_withdrawn),
                'balance': float(balance),
                'utilization_percentage': float(utilization_percentage),
                'pending_percentage': float(pending_percentage),
                'available_percentage': float(available_percentage),
                'total_commitment_percentage': float(total_commitment_percentage),
                'total_committed': float(withdrawn + to_be_withdrawn),
                'ace_count': ace_count,
                'avg_ace_amount': avg_ace_amount,
                'health_status': health['status'],
                'health_message': health['message'],
                'health_color': health['color'],
                'is_valid': validation['is_valid'],
                'validation_errors': validation['errors'],
                'validation_warnings': validation['warnings']
            }
            
        except Exception as e:
            logger.error(f"Budget summary calculation error: {str(e)}")
            return {
                'budget': budget,
                'error': f'Summary calculation failed: {str(e)}',
                'is_valid': False
            }


class BudgetTransactionService:
    """Service for handling budget transactions with proper validation"""
    
    @staticmethod
    @transaction.atomic
    def create_ace_with_budget_validation(ace_data: Dict, user) -> Tuple[bool, str, Optional[Ace2]]:
        """
        Create ACE with comprehensive budget validation
        
        Args:
            ace_data: Dictionary containing ACE data
            user: User creating the ACE
            
        Returns:
            Tuple of (success, message, ace_instance)
        """
        try:
            budget = ace_data.get('budget_id')
            amount = Decimal(str(ace_data.get('amount', 0)))
            
            # Validate budget first
            validation = BudgetIntegrityService.validate_ace_against_budget(amount, budget)
            
            if not validation['is_valid']:
                return False, '; '.join(validation['errors']), None
            
            # Lock the budget row to prevent concurrent modifications
            budget = AssetBudget.objects.select_for_update().get(pk=budget.pk)
            
            # Create ACE instance (simplified - you'll need to adapt this to your actual ACE creation logic)
            ace = Ace2.objects.create(
                amount=amount,
                budget_id=budget,
                requested_by=user,
                # Add other fields as needed
            )
            
            # Update budget atomically
            budget.to_be_withdrawn = (budget.to_be_withdrawn or 0) + amount
            budget.balance = (budget.balance or 0) - amount
            budget.save()
            
            # Create transaction record
            transaction_record = Transactions.objects.create(
                Ace_id2=ace,
                details_of_expenditure=ace_data.get('details_of_expenditure', ''),
                approval_status="created",
                amount=amount,
                budget=budget,
                region=user.region,
                section=user.section
            )
            
            logger.info(f"ACE {ace.Ace_id2} created successfully with budget validation")
            
            return True, "ACE created successfully", ace
            
        except Exception as e:
            logger.error(f"ACE creation error: {str(e)}")
            return False, f"ACE creation failed: {str(e)}", None
    
    @staticmethod
    @transaction.atomic
    def approve_ace_with_budget_update(ace: Ace2, user) -> Tuple[bool, str]:
        """
        Approve ACE with proper budget updates
        
        Args:
            ace: ACE instance to approve
            user: User approving the ACE
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Lock the budget row to prevent concurrent modifications
            budget = AssetBudget.objects.select_for_update().get(pk=ace.budget_id.pk)
            
            # Validate current state
            validation = BudgetIntegrityService.validate_budget_consistency(budget)
            if not validation['is_valid']:
                return False, f"Budget validation failed: {'; '.join(validation['errors'])}"
            
            # Update budget fields atomically
            budget.withdrawn = (budget.withdrawn or 0) + ace.amount
            budget.to_be_withdrawn = (budget.to_be_withdrawn or 0) - ace.amount
            budget.withdrawal_date = timezone.now().date()
            budget.save()
            
            # Update transaction status
            transaction_record = Transactions.objects.get(Ace_id2=ace)
            transaction_record.approval_status = "approved by General Manager"
            transaction_record.save()
            
            logger.info(f"ACE {ace.Ace_id2} approved successfully with budget update")
            
            return True, "ACE approved successfully"
            
        except Exception as e:
            logger.error(f"ACE approval error: {str(e)}")
            return False, f"ACE approval failed: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def reject_ace_with_budget_restoration(ace: Ace2, user) -> Tuple[bool, str]:
        """
        Reject ACE and restore budget allocation
        
        Args:
            ace: ACE instance to reject
            user: User rejecting the ACE
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Lock the budget row to prevent concurrent modifications
            budget = AssetBudget.objects.select_for_update().get(pk=ace.budget_id.pk)
            
            # Only adjust budget if it hasn't been adjusted already
            transaction_record = Transactions.objects.get(Ace_id2=ace)
            if transaction_record.approval_status != "Rejected":
                # Restore budget allocation
                budget.to_be_withdrawn = (budget.to_be_withdrawn or 0) - ace.amount
                budget.balance = (budget.balance or 0) + ace.amount
                budget.save()
                
                # Update transaction status
                transaction_record.approval_status = "Rejected"
                transaction_record.save()
                
                logger.info(f"ACE {ace.Ace_id2} rejected successfully with budget restoration")
            
            return True, "ACE rejected successfully"
            
        except Exception as e:
            logger.error(f"ACE rejection error: {str(e)}")
            return False, f"ACE rejection failed: {str(e)}"
