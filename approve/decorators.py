from django.contrib.auth.decorators import login_required
from approve.models import Step
from approve.forms import ApprovalForm

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