from django.core.management.base import BaseCommand
from approve.models import Workflow, Step
from it.users.models import Application, Roles

class Command(BaseCommand):
    help = 'Create ACE workflows for standard and high-value ACEs'

    def handle(self, *args, **options):
        # Get the ACE application
        ace_app, created = Application.objects.get_or_create(name='ace')
        
        # Create standard ACE workflow (existing)
        standard_workflow, created = Workflow.objects.get_or_create(
            name='ace',
            defaults={'application': ace_app}
        )
        
        # Create high-value ACE workflow with additional steps
        high_value_workflow, created = Workflow.objects.get_or_create(
            name='ace_high_value',
            defaults={'application': ace_app}
        )
        
        if created:
            self.stdout.write(f"Created high-value ACE workflow")
            
            # Get existing roles (you may need to adjust these based on your actual roles)
            try:
                roles = {
                    'pass': Roles.objects.get(role='pass', application='ace'),        # Section Head
                    'process': Roles.objects.get(role='process', application='ace'),  # Accounting Officer  
                    'check': Roles.objects.get(role='check', application='ace'),      # Finance Manager
                    'approve': Roles.objects.get(role='approve', application='ace'),  # General Manager
                }
            except Roles.DoesNotExist as e:
                self.stdout.write(self.style.ERROR(f"Required role not found: {e}"))
                return
            
            # Add FD and MD roles for high-value workflow
            # Create these roles if they don't exist
            try:
                fd_role = Roles.objects.get(role='fd', application='ace')
            except Roles.DoesNotExist:
                fd_role, _ = Roles.objects.get_or_create(
                    role='fd', 
                    application='ace',
                    defaults={'description': 'Finance Director'}
                )
                self.stdout.write(f"Created FD role for ACE application")
            
            try:
                md_role = Roles.objects.get(role='md', application='ace')
            except Roles.DoesNotExist:
                md_role, _ = Roles.objects.get_or_create(
                    role='md', 
                    application='ace',
                    defaults={'description': 'Managing Director'}
                )
                self.stdout.write(f"Created MD role for ACE application")
            
            # Create steps for high-value workflow (6 steps vs 4 for standard)
            # Standard workflow: Section Head -> Accounting Officer -> Finance Manager -> General Manager
            # Extended workflow: Section Head -> Accounting Officer -> Finance Manager -> General Manager -> Finance Director -> Managing Director
            steps_data = [
                (1, roles['pass'], "Section Head approval"),
                (2, roles['process'], "Accounting Officer review"),
                (3, roles['check'], "Finance Manager approval"),
                (4, roles['approve'], "General Manager approval"),
                (5, fd_role, "Finance Director approval"),
                (6, md_role, "Managing Director final approval"),
            ]
            
            # Clear existing steps for this workflow if any
            Step.objects.filter(workflow=high_value_workflow).delete()
            
            for step_num, role, description in steps_data:
                Step.objects.create(
                    workflow=high_value_workflow,
                    step=step_num,
                    approver=role,
                    to=description
                )
                
            self.stdout.write(f"Created {len(steps_data)} steps for high-value ACE workflow")
            
            # Display the workflow structure
            self.stdout.write(self.style.SUCCESS("High-value ACE workflow structure:"))
            for step_num, role, description in steps_data:
                self.stdout.write(f"  Step {step_num}: {description} ({role.role})")
        else:
            self.stdout.write("High-value ACE workflow already exists")
        
        # Also display standard workflow for comparison
        if Step.objects.filter(workflow=standard_workflow).exists():
            self.stdout.write(self.style.SUCCESS("Standard ACE workflow structure:"))
            for step in Step.objects.filter(workflow=standard_workflow).order_by('step'):
                self.stdout.write(f"  Step {step.step}: {step.to} ({step.approver.role})")
        
        self.stdout.write(self.style.SUCCESS('Successfully set up ACE workflows'))