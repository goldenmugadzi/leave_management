from django.core.management.base import BaseCommand
from django.db import transaction
from it.users.models import Application, Roles, UserProfile
from fault_locator.models import FaultLocatorRole

class Command(BaseCommand):
    help = 'Set up fault locator roles in the central user roles system'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Step 1: Create or get the fault_locator application
            application, created = Application.objects.get_or_create(
                name='fault_locator',
                defaults={'fullname': 'Fault Locator System'}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created application: {application.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Application already exists: {application.name}')
                )

            # Step 2: Create fault locator roles in the central system
            fault_locator_roles = [
                {
                    'role': 'senior_foreman',
                    'name': 'Senior Foreman',
                    'description': 'Can manage teams, devices, deployments, and assign faults system-wide. Full administrative access.'
                },
                {
                    'role': 'depot_foreperson',
                    'name': 'Depot Foreperson',
                    'description': 'Can assign faults to teams at their depot, report fault clearance, and verify completions.'
                },
                {
                    'role': 'team_leader',
                    'name': 'Team Leader',
                    'description': 'Can report fault location status, update work progress, and manage team activities.'
                },
                {
                    'role': 'team_member',
                    'name': 'Team Member',
                    'description': 'Can view team assignments and participate in fault location activities.'
                },
                {
                    'role': 'fault_reporter',
                    'name': 'Fault Reporter',
                    'description': 'Can report new faults and view fault status reports.'
                },
                {
                    'role': 'transport_manager',
                    'name': 'Transport Manager',
                    'description': 'Manages crane trucks and approves/assigns crane requests.'
                },
                {
                    'role': 'crane_operator',
                    'name': 'Crane Operator',
                    'description': 'Operates crane truck and submits job completion reports.'
                }
            ]

            created_roles = []
            for role_data in fault_locator_roles:
                role, created = Roles.objects.get_or_create(
                    role=role_data['role'],
                    application='fault_locator',
                    app_id=application,
                    defaults={
                        'name': role_data['name'],
                        'description': role_data['description']
                    }
                )
                
                if created:
                    created_roles.append(role)
                    self.stdout.write(
                        self.style.SUCCESS(f'Created role: {role.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Role already exists: {role.name}')
                    )

            # Step 3: Migrate existing FaultLocatorRole assignments to central system
            self.stdout.write('\n' + self.style.HTTP_INFO('Migrating existing role assignments...'))
            
            existing_assignments = FaultLocatorRole.objects.filter(is_active=True)
            migrated_count = 0
            
            for assignment in existing_assignments:
                try:
                    # Find the corresponding central role
                    central_role = Roles.objects.get(
                        role=assignment.role,
                        application='fault_locator'
                    )
                    
                    # Remove any existing fault_locator roles for this user
                    assignment.user.roles.filter(
                        application='fault_locator',
                        app_id=application
                    ).delete()
                    
                    # Add the new role
                    assignment.user.add_role(central_role, 'fault_locator')
                    migrated_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Migrated {assignment.user.username} -> {central_role.name}'
                        )
                    )
                    
                except Roles.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Could not find central role for: {assignment.role}'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error migrating {assignment.user.username}: {str(e)}'
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(f'\nMigrated {migrated_count} role assignments')
            )

            # Step 4: Display summary
            self.stdout.write('\n' + self.style.HTTP_INFO('SETUP COMPLETE'))
            self.stdout.write(f'Application: {application.name}')
            self.stdout.write(f'Total roles created: {len(created_roles)}')
            self.stdout.write(f'Total assignments migrated: {migrated_count}')
            
            # Step 5: Show next steps
            self.stdout.write('\n' + self.style.HTTP_INFO('NEXT STEPS:'))
            self.stdout.write('1. Update your role checking functions to use central roles')
            self.stdout.write('2. Use UserProfile.get_user_role_for_application("fault_locator")')
            self.stdout.write('3. Consider deprecating FaultLocatorRole model')
            self.stdout.write('4. Update admin interface to manage roles centrally')
