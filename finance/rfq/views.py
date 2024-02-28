from django.contrib import messages
from django.shortcuts import render, redirect

from django.apps import apps
from sweetify import sweetify

Sections = apps.get_model(app_label='users', model_name='Sections')
Districts = apps.get_model(app_label='users', model_name='Districts')
Depots = apps.get_model(app_label='users', model_name='Depots')
Regions = apps.get_model(app_label='users', model_name='Regions')
Roles = apps.get_model(app_label='users', model_name='Roles')
Designations = apps.get_model(app_label='users', model_name='Designations')
Notification = apps.get_model(app_label='users', model_name='Notification')
UserProfile = apps.get_model(app_label="users", model_name="UserProfile")
from django.contrib.auth.models import User

# Create your views here.
def index(request):

    # QuerySet Object
    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()

    custom_user_roles = {
        "non_conformity": {},
        "remittance_advice": {},
        "pettycash": {},
        "adjudication": {},
        "tokens": {},
        "tenders": {},
        "ace": {},
        "users": {},
        "rfq": {},
    }

    user_group_ids = user_profile.roles
    user_group_ids = user_group_ids.split(",") if user_group_ids else []
    for id in user_group_ids:

        role = Roles.objects.filter(id=id).first()

        if role.application =="rfq":
            custom_user_roles["rfq"]=role

    Rfq_role=custom_user_roles["rfq"].role
    print(Rfq_role)

    if Rfq_role == "RFQ Requester":
        return render(request, "rfq/rfq_requester.html")
    elif Rfq_role == "RFQ Section Head":
        return render(request, "rfq/rfq_authoriser.html")
    elif Rfq_role == "RFQ Finance Manager":
        return render(request, "rfq/rfq_fm.html")
    elif Rfq_role == "RFQ General Manager":
        return render(request, "rfq/rfq_gm.html")
    else:
        messages.error(request, 'you need to contact it to get a role in the ACE')
        sweetify.success(request,'you need to contact it to get a role in the ACE')
        return redirect("/")

    return redirect("/")
