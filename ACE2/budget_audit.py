"""
Budget Audit Logging System for ACE
Tracks all budget changes for accountability and debugging
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
import json
import logging

from .models import AssetBudget, Ace2, Asset_budget_Virament
from it.users.models import UserProfile


logger = logging.getLogger(__name__)


class BudgetAuditLog(models.Model):
    """Model to track all budget changes for audit purposes"""
    
    CHANGE_TYPES = [
        ('ACE_CREATED', 'ACE Created'),
        ('ACE_APPROVED', 'ACE Approved'),
        ('ACE_REJECTED', 'ACE Rejected'),
        ('VIRAMENT_CREATED', 'Virament Created'),
        ('VIRAMENT_APPROVED', 'Virament Approved'),
        ('VIRAMENT_REJECTED', 'Virament Rejected'),
        ('MANUAL_ADJUSTMENT', 'Manual Adjustment'),
        ('DATA_CORRECTION', 'Data Correction'),
        ('BUDGET_RECONCILIATION', 'Budget Reconciliation'),
    ]
    
    budget = models.ForeignKey(AssetBudget, on_delete=models.CASCADE, related_name='audit_logs')
    change_type = models.CharField(max_length=50, choices=CHANGE_TYPES)
    
    # Previous values
    old_allocated = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    old_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    old_to_be_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    old_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # New values
    new_allocated = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    new_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    new_to_be_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    new_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Change metadata
    amount_changed = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    reference_id = models.CharField(max_length=100, help_text="ACE ID, Virament ID, or other reference")
    description = models.TextField(help_text="Description of the change")
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Audit info
    changed_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['budget', 'timestamp']),
            models.Index(fields=['change_type', 'timestamp']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f"{self.change_type} - {self.budget.budget_name} - {self.timestamp}"
    
    @property
    def change_summary(self):
        """Get a human-readable summary of the change"""
        if self.change_type in ['ACE_CREATED', 'ACE_APPROVED', 'ACE_REJECTED']:
            return f"ACE {self.reference_id}: {self.change_type.replace('_', ' ')}"
        elif self.change_type in ['VIRAMENT_CREATED', 'VIRAMENT_APPROVED', 'VIRAMENT_REJECTED']:
            return f"Virament {self.reference_id}: {self.change_type.replace('_', ' ')}"
        else:
            return f"{self.change_type.replace('_', ' ')}: {self.description}"


class BudgetAuditService:
    """Service for logging budget changes"""
    
    @staticmethod
    def log_budget_change(budget: AssetBudget, change_type: str, reference_id: str, 
                         description: str, changed_by: UserProfile, amount_changed: Decimal = None,
                         old_values: dict = None, additional_data: dict = None, 
                         ip_address: str = None):
        """
        Log a budget change for audit purposes
        
        Args:
            budget: Budget that was changed
            change_type: Type of change (from CHANGE_TYPES)
            reference_id: Reference ID (ACE ID, Virament ID, etc.)
            description: Description of the change
            changed_by: User who made the change
            amount_changed: Amount that was changed
            old_values: Previous budget values
            additional_data: Additional metadata
            ip_address: IP address of the user
        """
        try:
            # Capture current values
            current_values = {
                'allocated': budget.allocated,
                'withdrawn': budget.withdrawn,
                'to_be_withdrawn': budget.to_be_withdrawn,
                'balance': budget.balance
            }
            
            # Create audit log entry
            audit_log = BudgetAuditLog.objects.create(
                budget=budget,
                change_type=change_type,
                old_allocated=old_values.get('allocated') if old_values else None,
                old_withdrawn=old_values.get('withdrawn') if old_values else None,
                old_to_be_withdrawn=old_values.get('to_be_withdrawn') if old_values else None,
                old_balance=old_values.get('balance') if old_values else None,
                new_allocated=current_values['allocated'],
                new_withdrawn=current_values['withdrawn'],
                new_to_be_withdrawn=current_values['to_be_withdrawn'],
                new_balance=current_values['balance'],
                amount_changed=amount_changed,
                reference_id=reference_id,
                description=description,
                additional_data=additional_data or {},
                changed_by=changed_by,
                ip_address=ip_address
            )
            
            logger.info(f"Budget audit log created: {audit_log}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create budget audit log: {str(e)}")
            return None
    
    @staticmethod
    def get_budget_change_history(budget: AssetBudget, limit: int = 50):
        """
        Get change history for a budget
        
        Args:
            budget: Budget to get history for
            limit: Maximum number of records to return
            
        Returns:
            QuerySet of BudgetAuditLog entries
        """
        return BudgetAuditLog.objects.filter(budget=budget).order_by('-timestamp')[:limit]
    
    @staticmethod
    def get_user_budget_actions(user: UserProfile, limit: int = 50):
        """
        Get budget actions performed by a user
        
        Args:
            user: User to get actions for
            limit: Maximum number of records to return
            
        Returns:
            QuerySet of BudgetAuditLog entries
        """
        return BudgetAuditLog.objects.filter(changed_by=user).order_by('-timestamp')[:limit]
    
    @staticmethod
    def get_budget_changes_by_type(change_type: str, limit: int = 50):
        """
        Get budget changes by type
        
        Args:
            change_type: Type of change to filter by
            limit: Maximum number of records to return
            
        Returns:
            QuerySet of BudgetAuditLog entries
        """
        return BudgetAuditLog.objects.filter(change_type=change_type).order_by('-timestamp')[:limit]
    
    @staticmethod
    def get_budget_changes_for_reference(reference_id: str):
        """
        Get all budget changes for a specific reference (ACE ID, Virament ID, etc.)
        
        Args:
            reference_id: Reference ID to search for
            
        Returns:
            QuerySet of BudgetAuditLog entries
        """
        return BudgetAuditLog.objects.filter(reference_id=reference_id).order_by('timestamp')
    
    @staticmethod
    def generate_budget_audit_report(budget: AssetBudget, start_date=None, end_date=None):
        """
        Generate a comprehensive audit report for a budget
        
        Args:
            budget: Budget to generate report for
            start_date: Start date for the report
            end_date: End date for the report
            
        Returns:
            Dict containing audit report data
        """
        try:
            # Build query
            query = BudgetAuditLog.objects.filter(budget=budget)
            
            if start_date:
                query = query.filter(timestamp__gte=start_date)
            if end_date:
                query = query.filter(timestamp__lte=end_date)
            
            audit_logs = query.order_by('-timestamp')
            
            # Generate summary statistics
            total_changes = audit_logs.count()
            change_types = audit_logs.values('change_type').distinct()
            
            change_summary = {}
            for change_type in change_types:
                count = audit_logs.filter(change_type=change_type['change_type']).count()
                change_summary[change_type['change_type']] = count
            
            # Calculate net changes
            net_changes = {
                'allocated': Decimal('0'),
                'withdrawn': Decimal('0'),
                'to_be_withdrawn': Decimal('0'),
                'balance': Decimal('0')
            }
            
            for log in audit_logs:
                if log.old_allocated is not None and log.new_allocated is not None:
                    net_changes['allocated'] += (log.new_allocated - log.old_allocated)
                if log.old_withdrawn is not None and log.new_withdrawn is not None:
                    net_changes['withdrawn'] += (log.new_withdrawn - log.old_withdrawn)
                if log.old_to_be_withdrawn is not None and log.new_to_be_withdrawn is not None:
                    net_changes['to_be_withdrawn'] += (log.new_to_be_withdrawn - log.old_to_be_withdrawn)
                if log.old_balance is not None and log.new_balance is not None:
                    net_changes['balance'] += (log.new_balance - log.old_balance)
            
            return {
                'budget': budget,
                'total_changes': total_changes,
                'change_summary': change_summary,
                'net_changes': net_changes,
                'audit_logs': audit_logs,
                'start_date': start_date,
                'end_date': end_date
            }
            
        except Exception as e:
            logger.error(f"Failed to generate budget audit report: {str(e)}")
            return None


# Utility functions for middleware/decorators
def capture_budget_state(budget: AssetBudget) -> dict:
    """Capture current budget state for audit logging"""
    return {
        'allocated': budget.allocated,
        'withdrawn': budget.withdrawn,
        'to_be_withdrawn': budget.to_be_withdrawn,
        'balance': budget.balance
    }


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
