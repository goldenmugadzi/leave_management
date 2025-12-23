"""
Diagnostic script to check why user ze263567 can't see approve button for ACE2510315644
Run with: python manage.py shell < check_ace_approval.py
"""

from it.users.models import UserProfile
from ACE2.models import Ace2
from approve.models import Step

# Get user
user = UserProfile.objects.filter(username='ze263567').first()
if not user:
    print("ERROR: User ze263567 not found!")
    exit()

print(f"\n{'='*60}")
print(f"USER: {user.username} ({user.get_full_name()})")
print(f"{'='*60}")
print(f"Region: {user.region}")
print(f"Section: {user.section}")
print(f"Cost Center: {user.cost_center}")
print(f"\nUser's ACE Roles:")
user_roles = user.roles.all()
ace_role = None
for role in user_roles:
    if role.application == "ace":
        print(f"  - {role.name} (role={role.role})")
        ace_role = role.role

if not ace_role:
    print("  WARNING: User has NO ACE roles!")

# Get ACE
ace = Ace2.objects.filter(Ace_id2='ACE2510315644').first()
if not ace:
    print("\nERROR: ACE2510315644 not found!")
    exit()

print(f"\n{'='*60}")
print(f"ACE: {ace.Ace_id2}")
print(f"{'='*60}")
print(f"Details: {ace.details_of_expenditure}")
print(f"Amount: {ace.amount}")
print(f"Region: {ace.region}")
print(f"Section: {ace.section}")
print(f"Cost Center: {ace.cost_center}")
print(f"Requested by: {ace.requested_by}")
print(f"Date created: {ace.date_created}")

if not ace.process:
    print("\nERROR: ACE has no workflow process assigned!")
    exit()

print(f"\nWorkflow: {ace.process.workflow.name}")

# Check approvals
approvals = ace.process.approval_set.all().order_by('step__step')
print(f"\nApproval History ({approvals.count()} steps completed):")
for approval in approvals:
    print(f"  Step {approval.step.step}: {approval.step.to}")
    print(f"    Status: {approval.approved}")
    print(f"    By: {approval.user.username if approval.user else 'N/A'}")
    print(f"    Date: {approval.approved_at if hasattr(approval, 'approved_at') else 'N/A'}")

# Check if rejected
if approvals.exists():
    last_approval = approvals.last()
    if last_approval.approved == "Rejected":
        print("\n*** ACE IS REJECTED - No approval button will show ***")
        exit()

# Get next step
last_approved_step = approvals.last().step.step if approvals.exists() else 0
next_step = last_approved_step + 1

total_steps = ace.process.workflow.step_set.count()
print(f"\nWorkflow Progress:")
print(f"  Last approved step: {last_approved_step}")
print(f"  Next step needed: {next_step}")
print(f"  Total steps: {total_steps}")

if next_step > total_steps:
    print("\n*** ACE IS FULLY APPROVED - No more steps needed ***")
    exit()

# Check the next step requirements
try:
    next_step_obj = Step.objects.get(step=next_step, workflow=ace.process.workflow)
    print(f"\nNext Step Details:")
    print(f"  Step {next_step_obj.step}: {next_step_obj.to}")
    print(f"  Required approver role: {next_step_obj.approver.name} (role={next_step_obj.approver.role})")
    
    # Check if user has this role
    if next_step_obj.approver in user_roles:
        print(f"\n✓ USER HAS THE REQUIRED ROLE - Approve button SHOULD appear")
        
        # Additional checks
        print(f"\nAdditional Checks:")
        print(f"  User role ({ace_role}) == 'pass': {ace_role == 'pass'}")
        print(f"  Next step is first step: {next_step == 1}")
        
        if ace_role == "pass":
            if next_step == 1:
                print("  → Button condition: Will show (pass role, first step)")
            elif next_step_obj:
                print("  → Button condition: Will show (pass role, has next step)")
        else:
            print(f"  → Button condition: Will show (role={ace_role}, has next step)")
            
    else:
        print(f"\n✗ USER DOES NOT HAVE THE REQUIRED ROLE")
        print(f"  User's ACE roles: {[r.name for r in user_roles if r.application == 'ace']}")
        print(f"  Required: {next_step_obj.approver.name}")
        print("\n*** This is why the approve button doesn't appear ***")
        
except Step.DoesNotExist:
    print(f"\nERROR: Next step {next_step} not found in workflow!")
    print("This could mean workflow is misconfigured")

print(f"\n{'='*60}\n")
