from django.core.management.base import BaseCommand
from it.users.models import UserProfile
from fault_locator.management.commands.audit_fault_locator_roles import infer_designation_role
from fault_locator.central_roles import FaultLocatorRoleManager

class Command(BaseCommand):
    help = 'Sync fault locator central roles based on user designations'

    def handle(self, *args, **options):
        users = UserProfile.objects.filter(designation__isnull=False)
        synced = 0
        
        for user in users:
            inferred_role = infer_designation_role(user)
            if inferred_role:
                role_constant = getattr(FaultLocatorRoleManager, inferred_role.upper(), None)
                if role_constant and not FaultLocatorRoleManager.has_role(user, role_constant):
                    try:
                        FaultLocatorRoleManager.assign_role(user, role_constant)
                        self.stdout.write(f"Assigned {inferred_role} to {user.username}")
                        synced += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error assigning {inferred_role} to {user.username}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Synced roles for {synced} users"))