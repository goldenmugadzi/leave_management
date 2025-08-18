from decimal import Decimal
import requests
from django.conf import settings
from django.core.cache import cache
from ACE2 import models
from finance.comparative_schedules.views import notify_user
from it.users.models import UserProfile, Regions, Roles
from ACE2.models import Ace2


def find_ace_section_head(section):
    all_users = UserProfile.objects.filter(section=section).all()
    if all_users:
        for user_profile in all_users:
            user_groups = user_profile.groups.values_list('name', flat=True)
            custom_user_roles = {"ace": {}}
            roles_ = user_profile.roles.all()
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()
                if role.application == "ace":
                    custom_user_roles["ace"] = role.role
            ace_role = str(custom_user_roles["ace"])
            if ace_role == "pass":
                userp = 'sh'
                sh = user_profile.username
                print(sh, ' is the section head')
                if sh:
                    return sh
    return None


def get_kc_dict():
    # Define the function logic here
    return {
        'key1': 'value1',
        'key2': 'value2',
        # Add more key-value pairs as needed
    }


def find_pettycash_section_head(section):
    all_users = UserProfile.objects.filter(section=section).all()
    if all_users:
        for user_profile in all_users:
            user_groups = user_profile.groups.values_list('name', flat=True)
            custom_user_roles = {"pettycash": {}}
            roles_ = user_profile.roles.all()
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()
                if role.application == "pettycash":
                    custom_user_roles["pettycash"] = role.role
            pettycash_role = str(custom_user_roles["pettycash"])
            if pettycash_role == "approve":
                userp = 'sh'
                sh = user_profile.username
                print(sh, ' is the section head')
                if sh:
                    return sh
    return None


def send_daily_gm_notifications():
    """
    Function to be scheduled for daily notification of pending items to GMs.
    Only notifies GMs about items in their specific region.
    """
    from django.http import HttpRequest
    
    # Create a mock request for the notification system
    request = HttpRequest()
    
    # Get all regions
    regions = Regions.objects.all()
    
    for region in regions:
        # Find general managers for this specific region only
        gm_users = UserProfile.objects.filter(
            region=region,
            roles__application="ace",
            roles__role="approve"
        ).all()
        
        if not gm_users:
            continue
        
        # Find pending items for this region's GM (filtered by region)
        pending_count = 0
        pending_aces = []
        
        for ace in Ace2.objects.filter(region=region):
            process = ace.process
            if not process or process.approval_set.filter(approved="Rejected").exists():
                continue
                
            if process.approval_set.exists():
                latest_approval = process.approval_set.last()
                current_step = latest_approval.step.step
                total_steps = process.workflow.step_set.count()
                
                if current_step == total_steps - 1:
                    pending_aces.append(ace)
                    pending_count += 1
        
        # Send a daily summary if there are pending items in this region
        if pending_count > 0:
            for gm in gm_users:
                msg = f"Daily reminder: You have {pending_count} ACE items awaiting your approval in {region.region}"
                url = "/ace/awaiting_my_action/"
                notify_user(gm, msg, "ACE", url, f"daily_gm_{region.id}", request)


def determine_ace_type(amount, currency='ZWL'):
    """
    Determine if ACE should be high-value type based on ZWL amount
    """
    # Convert amount to ZWL if it's in a different currency
    if currency.upper() == 'ZWL':
        zwl_amount = float(amount)
    else:
        # For now, assume all amounts are in ZWL or treat as ZWL
        zwl_amount = float(amount)

    if zwl_amount >= 1300000:  # 1,300,000 ZWL threshold
        return 'high_value', zwl_amount
    else:
        return 'standard', zwl_amount

def get_head_office_users(role_name):
    """
    Get users with specified role at head office level (Head Office region)
    For FD and MD who work across all regions
    """
    from it.users.models import Roles
    
    try:
        role = Roles.objects.get(role=role_name, application='ace')
        
        # Get users with this role who are at head office level
        # Head office users are in the "Head Office" region with ID 7
        try:
            head_office_region = Regions.objects.get(id=7)  # Head Office region ID
            head_office_users = UserProfile.objects.filter(
                roles=role,
                region=head_office_region
            )
        except Regions.DoesNotExist:
            # Fallback: if Head Office region with ID 7 not found, try by name
            head_office_region = Regions.objects.filter(region__iexact='Head Office').first()
            if head_office_region:
                head_office_users = UserProfile.objects.filter(
                    roles=role,
                    region=head_office_region
                )
            else:
                head_office_users = UserProfile.objects.none()
        
        return head_office_users
        
    except Roles.DoesNotExist:
        return UserProfile.objects.none()

def notify_head_office_approvers(ace_item, step_name, request):
    """
    Send notifications to head office approvers (FD/MD) for high-value ACEs
    """
    from ACE2.views import notify_user
    
    role_mapping = {
        'Finance Director approval (Head Office)': 'fd',
        'Managing Director final approval (Head Office)': 'md'
    }
    
    role_name = role_mapping.get(step_name)
    if not role_name:
        return
    
    head_office_users = get_head_office_users(role_name)
    
    for user in head_office_users:
        msg = f"High-Value ACE {ace_item.Ace_id2} ({ace_item.amount:,.2f} {ace_item.currency}) from {ace_item.region.region} requires your approval"
        url = f"/ace/ace_detail/{ace_item.Ace_id2}"
        notify_user(user, msg, "ACE", url, ace_item.Ace_id2, request)
        
    return len(head_office_users)

def get_regional_budget_impact_summary(ace_item):
    """
    Get a summary of budget impact for head office approvers
    """
    from ACE2.models import AssetBudget
    
    budget = ace_item.budget_id
    region = ace_item.region
    
    # Use existing budget fields that already account for all ACE statuses
    # to_be_withdrawn includes pending ACEs
    # withdrawn includes approved ACEs  
    # The budget system already handles rejected ACEs by reversing to_be_withdrawn
    
    # Get regional budget utilization using existing fields
    regional_budgets = AssetBudget.objects.filter(region=region, period=2025)
    total_allocated = regional_budgets.aggregate(total=models.Sum('allocated'))['total'] or 0
    total_withdrawn = regional_budgets.aggregate(total=models.Sum('withdrawn'))['total'] or 0
    total_pending = regional_budgets.aggregate(total=models.Sum('to_be_withdrawn'))['total'] or 0
    
    return {
        'budget_name': budget.budget_name,
        'region': region.region,
        'ace_amount': ace_item.amount,
        'ace_currency': ace_item.currency,
        'budget_balance': budget.balance,
        'current_budget_pending': budget.to_be_withdrawn,  # Pending ACEs for this specific budget
        'current_budget_withdrawn': budget.withdrawn,      # Approved ACEs for this specific budget
        'regional_budget_utilization': {
            'total_allocated': total_allocated,
            'total_withdrawn': total_withdrawn,
            'total_pending': total_pending,
            'utilization_percentage': (total_withdrawn / total_allocated * 100) if total_allocated > 0 else 0,
            'pending_percentage': (total_pending / total_allocated * 100) if total_allocated > 0 else 0
        }
    }

# Note: The following code should be added to approve/views.py approve_step function:
# if process.workflow.name == "big_ace2":
#     # Get current step info
#     latest_approval = process.approval_set.last()
#     current_step = latest_approval.step.step if latest_approval else 0
#     next_step = current_step + 1
#     
#     # Check if this is a head office step
#     step = Step.objects.get(workflow=process.workflow, step=next_step)
#     if step.to in ['Finance Director approval (Head Office)', 
#                    'Managing Director final approval (Head Office)']:
#         # Get the ACE item and trigger head office notifications
#         ace_item = process.ace2_set.last()
#         notify_head_office_approvers(ace_item, step.to, request)
