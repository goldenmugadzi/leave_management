from it.users.models import UserProfile, Roles


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
