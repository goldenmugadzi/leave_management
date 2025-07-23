"""
Setup script for Sanction For Test workflow roles and steps
Run this to create the necessary roles and workflow configuration
"""

from django.core.management.base import BaseCommand
from it.users.models import Application, Roles
from approve.models import Workflow, Step


class Command(BaseCommand):
    help = 'Setup Sanction For Test workflow roles and steps'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Sanction For Test workflow...')

        # Create or get the application
        app, created = Application.objects.get_or_create(
            name='sanction_for_test',
            defaults={'fullname': 'Sanction For Test Forms'}
        )
        if created:
            self.stdout.write(f'Created application: {app.fullname}')
        else:
            self.stdout.write(f'Application already exists: {app.fullname}')

        # Create roles for sanction workflow
        roles_to_create = [
            {
                'role': 'sanction_responsible_official',
                'name': 'Responsible Official (Sanction)',
                'description': 'Can issue/declare sanction for test forms',
                'application': 'sanction_for_test'
            },
            {
                'role': 'sanction_receiver',
                'name': 'Sanction Receiver',
                'description': 'Can receive sanction for test forms',
                'application': 'sanction_for_test'
            },
            {
                'role': 'sanction_clearer',
                'name': 'Sanction Clearer',
                'description': 'Can clear sanction for test forms',
                'application': 'sanction_for_test'
            },
            {
                'role': 'sanction_controller',
                'name': 'Sanction Controller',
                'description': 'Can cancel sanction for test forms',
                'application': 'sanction_for_test'
            },
        ]

        created_roles = []
        for role_data in roles_to_create:
            role, created = Roles.objects.get_or_create(
                role=role_data['role'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'application': role_data['application'],
                    'app_id': app
                }
            )
            created_roles.append(role)
            if created:
                self.stdout.write(f'Created role: {role.name}')
            else:
                self.stdout.write(f'Role already exists: {role.name}')

        # Create workflow
        workflow, created = Workflow.objects.get_or_create(
            name='Sanction For Test Approval',
            defaults={'application': app}
        )
        if created:
            self.stdout.write(f'Created workflow: {workflow.name}')
        else:
            self.stdout.write(f'Workflow already exists: {workflow.name}')

        # Create workflow steps
        steps_to_create = [
            {
                'step': 1,
                'approver': created_roles[0],  # Responsible Official
                'to': 'Issue/Declaration',
            },
            {
                'step': 2,
                'approver': created_roles[1],  # Receiver
                'to': 'Receipt',
            },
            {
                'step': 3,
                'approver': created_roles[2],  # Clearer
                'to': 'Clearance',
            },
            {
                'step': 4,
                'approver': created_roles[3],  # Controller (for cancellation)
                'to': 'Cancellation (Optional)',
            },
        ]

        for step_data in steps_to_create:
            step, created = Step.objects.get_or_create(
                workflow=workflow,
                step=step_data['step'],
                defaults={
                    'approver': step_data['approver'],
                    'to': step_data['to']
                }
            )
            if created:
                self.stdout.write(f'Created step {step.step}: {step.approver.name} -> {step.to}')
            else:
                self.stdout.write(f'Step {step.step} already exists: {step.approver.name} -> {step.to}')

        self.stdout.write(self.style.SUCCESS('Sanction For Test workflow setup complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Assign users to the created roles using the admin interface')
        self.stdout.write('2. Configure role matrix for cost centers if needed')
        self.stdout.write('3. Test the workflow by creating a sanction form')
