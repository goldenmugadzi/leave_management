"""
Management command to process role delegations
Handles activation, expiry, and notifications
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from it.users.models import RoleDelegation, DelegationNotification, UserProfile
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process role delegations - activate, expire, and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Process delegations that need to be activated
        self.activate_delegations(now, dry_run)
        
        # Process delegations that need to be expired
        self.expire_delegations(now, dry_run)
        
        # Send reminder notifications
        self.send_reminder_notifications(now, dry_run)
        
        self.stdout.write(
            self.style.SUCCESS('Delegation processing completed successfully')
        )

    def activate_delegations(self, now, dry_run=False):
        """Activate delegations that are approved and past their start date"""
        delegations_to_activate = RoleDelegation.objects.filter(
            status='APPROVED',
            start_date__lte=now,
            is_active=True
        )
        
        activated_count = 0
        for delegation in delegations_to_activate:
            if not dry_run:
                if delegation.activate():
                    # Create notification
                    DelegationNotification.objects.create(
                        delegation=delegation,
                        recipient=delegation.delegator,
                        notification_type='DELEGATION_ACTIVATED',
                        message=f"Your delegation to {delegation.delegatee.get_full_name()} is now active"
                    )
                    
                    DelegationNotification.objects.create(
                        delegation=delegation,
                        recipient=delegation.delegatee,
                        notification_type='DELEGATION_ACTIVATED',
                        message=f"Role delegation from {delegation.delegator.get_full_name()} is now active"
                    )
                    
                    activated_count += 1
                    logger.info(f"Activated delegation {delegation.id}")
            else:
                activated_count += 1
                self.stdout.write(f"Would activate delegation {delegation.id}")
        
        if activated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Activated {activated_count} delegations')
            )

    def expire_delegations(self, now, dry_run=False):
        """Expire delegations that are past their end date"""
        delegations_to_expire = RoleDelegation.objects.filter(
            status='ACTIVE',
            end_date__lte=now,
            is_active=True
        )
        
        expired_count = 0
        for delegation in delegations_to_expire:
            if not dry_run:
                if delegation.expire():
                    # Create notification
                    DelegationNotification.objects.create(
                        delegation=delegation,
                        recipient=delegation.delegator,
                        notification_type='DELEGATION_EXPIRED',
                        message=f"Your delegation to {delegation.delegatee.get_full_name()} has expired"
                    )
                    
                    DelegationNotification.objects.create(
                        delegation=delegation,
                        recipient=delegation.delegatee,
                        notification_type='DELEGATION_EXPIRED',
                        message=f"Role delegation from {delegation.delegator.get_full_name()} has expired"
                    )
                    
                    expired_count += 1
                    logger.info(f"Expired delegation {delegation.id}")
            else:
                expired_count += 1
                self.stdout.write(f"Would expire delegation {delegation.id}")
        
        if expired_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Expired {expired_count} delegations')
            )

    def send_reminder_notifications(self, now, dry_run=False):
        """Send reminder notifications for delegations expiring soon"""
        # Send reminders 24 hours before expiry
        reminder_time = now + timezone.timedelta(hours=24)
        
        delegations_expiring_soon = RoleDelegation.objects.filter(
            status='ACTIVE',
            end_date__lte=reminder_time,
            end_date__gt=now,
            is_active=True
        )
        
        reminder_count = 0
        for delegation in delegations_expiring_soon:
            # Check if reminder was already sent
            existing_reminder = DelegationNotification.objects.filter(
                delegation=delegation,
                notification_type='DELEGATION_REMINDER',
                sent_at__date=now.date()
            ).exists()
            
            if not existing_reminder:
                if not dry_run:
                    # Create reminder notifications
                    DelegationNotification.objects.create(
                        delegation=delegation,
                        recipient=delegation.delegator,
                        notification_type='DELEGATION_REMINDER',
                        message=f"Your delegation to {delegation.delegatee.get_full_name()} expires on {delegation.end_date.strftime('%Y-%m-%d %H:%M')}"
                    )
                    
                    DelegationNotification.objects.create(
                        delegation=delegation,
                        recipient=delegation.delegatee,
                        notification_type='DELEGATION_REMINDER',
                        message=f"Role delegation from {delegation.delegator.get_full_name()} expires on {delegation.end_date.strftime('%Y-%m-%d %H:%M')}"
                    )
                    
                    reminder_count += 1
                    logger.info(f"Sent reminder for delegation {delegation.id}")
                else:
                    reminder_count += 1
                    self.stdout.write(f"Would send reminder for delegation {delegation.id}")
        
        if reminder_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Sent {reminder_count} reminder notifications')
            )
