from django.shortcuts import render

from django.apps import apps
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
    return render(request, 'rfq/index.html')
