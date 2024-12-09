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
