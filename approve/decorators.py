from django.contrib.auth.decorators import login_required,user_passes_test
from approve.models import Step
from approve.forms import ApprovalForm
from functools import wraps
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import  redirect

@login_required
def ApprovalDetails(request, object):
    approvalForm=None
    to=None
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute
    
    try:
        last_approved = object.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    
    next_step = last_approved + 1
    
    try:
        newStep= Step.objects.get(step=next_step, workflow=object.process.workflow, approver__in=user_roles)
        if newStep and request.user.section==object.section and next_step==1:
            approvalForm = ApprovalForm 
            to=newStep.to
        elif newStep:
            approvalForm = ApprovalForm
            to=newStep.to
    except Step.DoesNotExist:
        pass
    approved_steps = object.process.approval_set.all().values_list('step__step', flat=True)
    return approved_steps, approvalForm, to
# check if all the steps have been approved
def all_approved(object):
    print(object.process.approval_set.all().count())
    return object.process.approval_set.all().count() == object.process.workflow.step_set.all().count()

def checklist_roles(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not any(role.application == 'non_conformity' and role.role == 'supervisor' for role in user.roles.all()):
            messages.error(request, 'You must be a supervisor for nonconformity to edit this page.')
            return redirect('nonconformity:checklist')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def allowed_roles(allowed_roles, app_names):
    def decorator(view_func):
        @user_passes_test(lambda user: user.roles.filter(Q(name__in=allowed_roles) and Q(app_id__name__in=app_names)).exists())
        def wrapper(request, *args, **kwargs):
            messages.error(request, 'You are not authorised to access this page. Please contact the administrator for assistance.')
            return redirect('/')

        return wrapper
    return decorator
