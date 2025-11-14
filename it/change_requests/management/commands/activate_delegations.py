"""
Management command to activate approved delegations when their start_date arrives.

This command should be run periodically (e.g., every hour via cron) to:
1. Find delegations with status='APPROVED' where start_date <= now < end_date
2. Update their status to 'ACTIVE'
3. Send activation notifications to delegator and delegatee
4. Log all activation actions

Usage:
    python manage.py activate_delegations
    python manage.py activate_delegations --dry-run  # Preview without applying
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from it.users.models import RoleDelegation, DelegationNotification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Activate approved delegations when their start_date arrives'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview delegations that would be activated without making changes',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find delegations ready to be activated
        # Status must be APPROVED, start_date must have arrived, and must not be expired
        delegations_to_activate = RoleDelegation.objects.filter(
            status='APPROVED',
            start_date__lte=now,
            end_date__gt=now,
            is_active=True
        ).select_related('delegator', 'delegatee').prefetch_related('roles', 'applications')
        
        count = delegations_to_activate.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No delegations ready to activate'))
            return
        
        self.stdout.write(f'Found {count} delegation(s) ready to activate')
        
        activated_count = 0
        error_count = 0
        
        for delegation in delegations_to_activate:
            try:
                if dry_run:
                    self.stdout.write(
                        f'  [DRY RUN] Would activate delegation {delegation.id}: '
                        f'{delegation.delegator.username} → {delegation.delegatee.username} '
                        f'(Start: {delegation.start_date}, End: {delegation.end_date})'
                    )
                    activated_count += 1
                else:
                    with transaction.atomic():
                        # Activate the delegation
                        delegation.status = 'ACTIVE'
                        delegation.save()
                        
                        # Create notification for delegatee
                        DelegationNotification.objects.create(
                            delegation=delegation,
                            recipient=delegation.delegatee,
                            notification_type='DELEGATION_ACTIVATED',
                            message=f"Role delegation from {delegation.delegator.get_full_name()} is now active"
                        )
                        
                        # Create notification for delegator
                        DelegationNotification.objects.create(
                            delegation=delegation,
                            recipient=delegation.delegator,
                            notification_type='DELEGATION_ACTIVATED',
                            message=f"Your role delegation to {delegation.delegatee.get_full_name()} is now active"
                        )
                        
                        logger.info(
                            f"Activated delegation {delegation.id}: "
                            f"{delegation.delegator.username} → {delegation.delegatee.username}"
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Activated delegation {delegation.id}: '
                                f'{delegation.delegator.username} → {delegation.delegatee.username}'
                            )
                        )
                        activated_count += 1
                        
            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error activating delegation {delegation.id}: {str(e)}",
                    exc_info=True
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Failed to activate delegation {delegation.id}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write('')
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN SUMMARY: Would have activated {activated_count} delegation(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'SUMMARY: Successfully activated {activated_count} delegation(s)'
                )
            )
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'  Errors: {error_count} delegation(s) failed to activate'
                    )
                )
        
        # Also check for delegations that should be expired
        self._expire_delegations(dry_run, now)
    
    def _expire_delegations(self, dry_run, now):
        """Expire active delegations that have passed their end_date"""
        delegations_to_expire = RoleDelegation.objects.filter(
            status='ACTIVE',
            end_date__lte=now
        ).select_related('delegator', 'delegatee')
        
        expire_count = delegations_to_expire.count()
        
        if expire_count == 0:
            return
        
        self.stdout.write('')
        self.stdout.write(f'Found {expire_count} delegation(s) to expire')
        
        expired_count = 0
        error_count = 0
        
        for delegation in delegations_to_expire:
            try:
                if dry_run:
                    self.stdout.write(
                        f'  [DRY RUN] Would expire delegation {delegation.id}: '
                        f'{delegation.delegator.username} → {delegation.delegatee.username} '
                        f'(Ended: {delegation.end_date})'
                    )
                    expired_count += 1
                else:
                    with transaction.atomic():
                        # Expire the delegation
                        delegation.status = 'EXPIRED'
                        delegation.save()
                        
                        # Create notification for delegatee
                        DelegationNotification.objects.create(
                            delegation=delegation,
                            recipient=delegation.delegatee,
                            notification_type='DELEGATION_EXPIRED',
                            message=f"Role delegation from {delegation.delegator.get_full_name()} has expired"
                        )
                        
                        # Create notification for delegator
                        DelegationNotification.objects.create(
                            delegation=delegation,
                            recipient=delegation.delegator,
                            notification_type='DELEGATION_EXPIRED',
                            message=f"Your role delegation to {delegation.delegatee.get_full_name()} has expired"
                        )
                        
                        logger.info(
                            f"Expired delegation {delegation.id}: "
                            f"{delegation.delegator.username} → {delegation.delegatee.username}"
                        )
                        
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⏰ Expired delegation {delegation.id}: '
                                f'{delegation.delegator.username} → {delegation.delegatee.username}'
                            )
                        )
                        expired_count += 1
                        
            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error expiring delegation {delegation.id}: {str(e)}",
                    exc_info=True
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Failed to expire delegation {delegation.id}: {str(e)}'
                    )
                )
        
        # Summary for expirations
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would have expired {expired_count} delegation(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Successfully expired {expired_count} delegation(s)'
                )
            )
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'  Errors: {error_count} delegation(s) failed to expire'
                    )
                )

