from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import redirect, render

from it.change_requests.models import CRApproval, ChangeRequest, NewProfile
from it.users.models import Application, CostCenter, Depots, Designations, Districts, Regions, Roles, Sections, UserProfile
from django.db.models import Q
from django.contrib import messages
import traceback
from django.core.paginator import Paginator

# Create your views here.
def create_change_request(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
    user_groups = list(l)

    # get roles
    all_roles = {}
    user_applications = Application.objects.all()
    for app in user_applications:
        app_roles = Roles.objects.filter(app_id=app.id).all()
        all_roles[app.name] = app_roles
    
    # get designations
    user_designations = Designations.objects.all()
    sections = Sections.objects.all()
    cost_centers = CostCenter.objects.all()
    districts = Districts.objects.all()
    regions = Regions.objects.all()
    
    return render(request, 'change_requests/create_change_request.html',
            {
                "user_roles": all_roles,
                "user_applications": user_applications,
                "user_designations": user_designations,
                "cost_centers": cost_centers,
                "sections": sections,
                "districts": districts,
                "regions": regions,
                "user_title": user_title,
                "user_groups": user_groups,
            })
    
def create_new_profile(request):
    try:
        requestor_username = request.user.username
        change_reason = request.POST.get('change_reason')
        change_description = request.POST.get('change_description')
        profile_username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        designation_ = request.POST.get('designation')
        section_ = request.POST.get('section')
        cost_center = request.POST.get('cost_center')
        district_ = request.POST.get('district')
        region_ = request.POST.get('region')

        region = Regions.objects.filter(id=region_).first()
        cost_center_ = CostCenter.objects.filter(id=cost_center).first() if cost_center else None
        district = Districts.objects.filter(code=district_).first() if district_ else None
        section = Sections.objects.filter(code=section_).first() if section_ else None
        designation = Designations.objects.filter(id=designation_).first() if designation_ else None

        user = NewProfile(
            username=profile_username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            designation=designation,
            cost_center= cost_center_,
            section=section,
            district=district,
            region=region,
            created_at=datetime.now()
        )

        user.save()

        # Get actual Role objects:
        user_applications = Application.objects.all()
        roles = [role for role in [request.POST.get(app.name) for app in user_applications if request.POST.get(app.name) != ""] if role and role != ""]  
        print("roles: ", roles)    
        role_objects = Roles.objects.filter(id__in=roles)  # Example of retrieving roles
        user.roles.add(*role_objects)
        user.save()

        cr_id = "CR-" + datetime.now().strftime("%Y%m%d%I%M%S")
        change_request = ChangeRequest(
            cr_id=cr_id,
            change_type="New Profile",
            new_profile=user,
            change_description=change_description,
            change_reason=change_reason,
            creator_designation=designation,
            created_by=request.user,
            region=region,
            cost_center=cost_center_,
            created_at=datetime.now()
        )
        change_request.save()
        
        messages.success(request, "Change request submitted successfully")
    except Exception as ex:
        print("error: ", ex)
        messages.error(request, "An error occurred while submitting the change request")
        
    return redirect("/change_requests/create_change_request")

def new_profile_request(request):
    if request.method == "GET":
        change_request = ChangeRequest.objects.get(cr_id=request.GET['i'])
        if change_request.new_profile:
                print("change_request.new_profile.roles.all(): ", change_request.new_profile.roles.all(), change_request.new_profile.roles)
                active_roles = {role.app_id.name: role for role in change_request.new_profile.roles.all() if role.app_id}

                new_user = {
                    "id": change_request.new_profile.pk,
                    "username": change_request.new_profile.username,
                    "firstname": change_request.new_profile.first_name,
                    "lastname": change_request.new_profile.last_name,
                    "email": change_request.new_profile.email,
                    "section": Sections.objects.filter(id=change_request.new_profile.section.id).first() if change_request.new_profile.section else None,
                    "district": Districts.objects.filter(id=change_request.new_profile.district.id).first() if change_request.new_profile.district else None,
                    "region": Regions.objects.filter(id=change_request.new_profile.region.id).first() if change_request.new_profile.region else None,
                    "cost_center": CostCenter.objects.filter(id=change_request.new_profile.cost_center.id).first() if change_request.new_profile.cost_center else None,
                    "roles": active_roles,
                    "designation": Designations.objects.filter(id=change_request.new_profile.designation.id).first() if change_request.new_profile.designation else None,
                }

                all_roles = {app.name: Roles.objects.filter(app_id=app.id).all() for app in Application.objects.all()}
                cr = {
                    "user": new_user,
                    "cr_id": change_request.cr_id,
                    "change_reason": change_request.change_reason,
                    "change_description": change_request.change_description,
                    "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                    "creator_designation": change_request.creator_designation.description,
                    "created_at": change_request.created_at
                }
                return render(
                    request,
                    "change_requests/new_profile_request.html",
                    {
                        "user_roles": all_roles,
                        "user_applications": Application.objects.all(),
                        "user_designations": Designations.objects.all(),
                        "sections": Sections.objects.all(),
                        "districts": Districts.objects.all(),
                        "regions": Regions.objects.all(),
                        "user_title": request.user.get_full_name(),
                        "user_groups": list(request.user.groups.values_list('name', flat=True)),
                        "cr": cr
                    }
                )

def view_profile_request(request):
    if request.method == "GET":
        change_request = ChangeRequest.objects.get(cr_id=request.GET['i'])
        if change_request.new_profile:
                print("change_request.new_profile.roles.all(): ", change_request.new_profile.roles.all(), change_request.new_profile.roles)
                active_roles = {role.app_id.name: role for role in change_request.new_profile.roles.all() if role.app_id}

                new_user = {
                    "id": change_request.new_profile.pk,
                    "username": change_request.new_profile.username,
                    "firstname": change_request.new_profile.first_name,
                    "lastname": change_request.new_profile.last_name,
                    "email": change_request.new_profile.email,
                    "section": Sections.objects.filter(id=change_request.new_profile.section.id).first() if change_request.new_profile.section else None,
                    "district": Districts.objects.filter(id=change_request.new_profile.district.id).first() if change_request.new_profile.district else None,
                    "region": Regions.objects.filter(id=change_request.new_profile.region.id).first() if change_request.new_profile.region else None,
                    "cost_center": CostCenter.objects.filter(id=change_request.new_profile.cost_center.id).first() if change_request.new_profile.cost_center else None,
                    "roles": active_roles,
                    "designation": Designations.objects.filter(id=change_request.new_profile.designation.id).first() if change_request.new_profile.designation else None,
                }

                all_roles = {app.name: Roles.objects.filter(app_id=app.id).all() for app in Application.objects.all()}
                cr = {
                    "user": new_user,
                    "cr_id": change_request.cr_id,
                    "change_reason": change_request.change_reason,
                    "change_description": change_request.change_description,
                    "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                    "creator_designation": change_request.creator_designation.description,
                    "created_at": change_request.created_at
                }
                
                # get all approvals
                cr_approvals = CRApproval.objects.filter(cr_id=change_request).all()
                section_head_awaiting_action = True
                it_section_head_awaiting_action = True
                for approval in cr_approvals:
                    if approval.approver_role.role == "section_head":
                        section_head_awaiting_action = False
                    if approval.approver_role.role == "it_section_head":
                        it_section_head_awaiting_action = False
                
                print("section_head_awaiting_action: ", section_head_awaiting_action)
                print("it_section_head_awaiting_action: ", it_section_head_awaiting_action)
                requestor = UserProfile.objects.filter(username=request.user.username).first()
                requestor_role = requestor.get_user_roles_for_application("change_requests")

                return render(
                    request,
                    "change_requests/view_profile_request.html",
                    {
                        "user_roles": all_roles,
                        "requestor_role": requestor_role,
                        "section_head_awaiting_action": section_head_awaiting_action,
                        "it_section_head_awaiting_action": it_section_head_awaiting_action,
                        "user_applications": Application.objects.all(),
                        "user_designations": Designations.objects.all(),
                        "sections": Sections.objects.all(),
                        "districts": Districts.objects.all(),
                        "regions": Regions.objects.all(),
                        "cr_approvals": cr_approvals,
                        "user_title": request.user.get_full_name(),
                        "user_groups": list(request.user.groups.values_list('name', flat=True)),
                        "cr": cr
                    }
                )


def update_new_profile_request(request):
    if request.method == "POST":
        try:
            cr_id = request.POST.get('cr_id')
            change_reason = request.POST.get('change_reason')
            change_description = request.POST.get('change_description')
            change_request = ChangeRequest.objects.filter(cr_id=cr_id).first()
            if not change_request:
                messages.error(request, "Change request not found")
                return redirect("/change_requests/change_request_index")
            else:
                
                change_request.change_reason = change_reason if change_reason else change_request.change_reason
                change_request.change_description = change_description if change_reason else change_request.change_description
                change_request.save()
            
                user_data = {
                    'first_name': request.POST.get('firstname'),
                    'last_name': request.POST.get('lastname'),
                    'username': request.POST.get('username'),
                    'email': request.POST.get('email'),
                    'region': Regions.objects.filter(id=request.POST.get('region')).first(),
                    'cost_center': CostCenter.objects.filter(id=request.POST.get('cost_center')).first() if request.POST.get('cost_center') not in ["Select Cost Center", ""] else None,
                    'district': Districts.objects.filter(id=request.POST.get('district')).first() if request.POST.get('district') not in ["Select District", ""] else None,
                    'section': Sections.objects.filter(code=request.POST.get('section')).first(),
                    'designation': Designations.objects.filter(id=request.POST.get('designation')).first() if request.POST.get('designation') not in ["Select Designation", ""] else None
                }

                if change_request.new_profile:
                    user_id = change_request.new_profile.id
                    user = NewProfile.objects.filter(id=user_id).first()
                    for field, value in user_data.items():
                        if value:
                            setattr(user, field, value)

                    user.save()

                    roles = [role for role in [request.POST.get(app.name) for app in Application.objects.all() if request.POST.get(app.name) != 'Select Role'] if role and role != ""]
                    user.roles.clear()
                    user.roles.add(*Roles.objects.filter(id__in=roles))
                messages.success(request, "Change Request updated successfully")
        except Exception as ex:
            traceback.print_exc()
            print("save user error", ex)
            messages.error(request, "An error occurred while saving the change request")
    
        return redirect("/change_requests/change_request_index")
    
def approve_profile_request(request):
    if request.method == "POST":
        try:
            cr_id = request.POST.get('cr_id')
            requestor = UserProfile.objects.filter(username=request.user.username).first()
            user_role = requestor.get_user_roles_for_application("change_requests")
            change_request = ChangeRequest.objects.filter(cr_id=cr_id).first()
            if 'APPROVE' in request.POST:
                # The "APPROVE CHANGE REQUEST" button was clicked
                if not change_request:
                    messages.error(request, "Change request not found")
                    return redirect("/change_requests/change_request_index")
                else:
                    
                    if user_role == "section_head":
                        cr_approval = CRApproval(
                            cr_id=change_request,
                            approver=request.user,
                            approver_role=requestor.get_user_role_for_application("change_requests"),
                            approval_status=True,
                            approval_date=datetime.now()
                        )
                        cr_approval.save()
                        messages.success(request, "Change Request approved successfully")
                    else:
                        messages.error(request, "Error. Please check your Change Request role")
                    
                    return redirect("/change_requests/change_request_index")
                    
            elif 'REJECT' in request.POST:
                # The "REJECT CHANGE REQUEST" button was clicked
                cr_approval = CRApproval(
                    cr_id=change_request,
                    approver=request.user,
                    approver_role=requestor.get_user_role_for_application("change_requests"),
                    approval_status=False,
                    comment=request.POST.get('comment'),
                    approval_date=datetime.now()
                )
            elif 'APPLY' in request.POST:
                # The "APPLY CHANGE REQUEST" button was clicked
                if user_role == "it_section_head":
                    cr_approval = CRApproval(
                        cr_id=change_request,
                        approver=request.user,
                        approver_role=requestor.get_user_role_for_application("change_requests"),
                        approval_status=True,
                        approval_date=datetime.now()
                    )
                    cr_approval.save()
                    messages.success(request, "Change Request approved successfully")
                    cr_type = change_request.change_type
                    
                    if cr_type == "New Profile":
                        new_profile = change_request.new_profile
                        user = UserProfile(
                            username=new_profile.username,
                            first_name=new_profile.first_name,
                            last_name=new_profile.last_name,
                            email=new_profile.email,
                            designation=new_profile.designation,
                            cost_center=new_profile.cost_center,
                            section=new_profile.section,
                            district=new_profile.district,
                            region=new_profile.region
                        )
                        user.save()
                        user.roles.add(*new_profile.roles.all())
                        user.set_password("Password@2024")
                        user.save()
                        messages.success(request, "Change Request applied successfully")
                    
                    return redirect("/change_requests/change_request_index")

        except Exception as ex:
            print("error: ", ex)
            messages.error(request, "An error occurred while approving the change request " + ex)
    return redirect("/change_requests/change_request_index")

def change_request_index(request):

    user_page = 'change_requests/change_request_index.html'
    user_title = request.user.get_full_name()

    return render(
        request,
        user_page,
        {
            "title": "Change Requests",
            "user_title": user_title,
        })
    
def datatable_data(request):
    draw = int(request.GET.get('draw', default=1))
    start = int(request.GET.get('start', default=0))
    length = int(request.GET.get('length', default=10))
    search_value = request.GET.get('search[value]', default='')
    user = request.user

    if user.region:
        # Fetch your data from the model
        records = ChangeRequest.objects.filter(region=user.region).all()
        # Filter based on search value
        if search_value:
            records = records.filter(
            Q(change_reason__icontains=search_value) |
            Q(new_profile__first_name__icontains=search_value) |
            Q(new_profile__last_name__icontains=search_value) |
            Q(new_profile__email__icontains=search_value) |
            Q(new_profile__username__icontains=search_value)
            )

        # Total number of records before filtering
        total = records.count()

        # Sorting
        order_column = request.GET.get('order[0][column]')
        order = request.GET.get('order[0][dir]')
        if order_column:
            column_name = request.GET.get(f'columns[{order_column}][data]')
            if order == 'desc':
                column_name = f'-{column_name}'
            records = records.order_by(column_name)

        # Pagination
        paginator = Paginator(records, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)

        # Prepare response
        data = []
        for obj in page_obj:
            try:
                change_requests = {
                    "cr_id": obj.cr_id,
                    "change_type": obj.change_type,
                    "change_description": obj.change_description,
                    "change_reason": obj.change_reason,
                    "creator_designation": obj.creator_designation.description,
                    "created_by": obj.created_by.first_name + " " + obj.created_by.last_name,
                    "region": obj.region.region,
                    "cost_center": obj.cost_center.name,
                    "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M"),
                }

                data.append(change_requests)
            except Exception as ex:
                print("Cost Center Error: ", ex)

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        })
