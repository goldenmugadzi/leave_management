from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q, Count, Avg, Max
from datetime import datetime, timedelta
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

# Import models from various apps
from it.users.models import UserProfile, Roles, Application
from approve.models import Process, Step, Approval, Workflow
from ACE2.models import Ace2
from finance.PettyCash.models import Pettycash
from tokens.models import Token
from finance.purchase_request.models import PurchaseRequest
from it.change_requests.models import ChangeRequest
from safety.models import SafetyMonthlyReport
from Asset_Register.models import ZetdcAssets
from Hardware_Faults.models import Employee as HardwareFault
from Transport.models import TransportAssets
from .models import (
    DashboardPreference, ActionItemMetrics, DashboardWidget,
    DashboardMetric, WeeklySales, WeeklyOutage, WeeklyFaultMaintenance, TopDebtor
)


@login_required
def action_dashboard(request):
    """
    Main action dashboard showing role-based applications and pending actions
    """
    user = request.user
    user_profile = get_object_or_404(UserProfile, id=user.id)
    user_roles = user_profile.roles.all()
    
    # Get or create dashboard preferences
    preferences, created = DashboardPreference.objects.get_or_create(user=user_profile)
    
    # Get all applications the user has access to with metrics
    accessible_apps = get_user_applications_with_metrics(user_roles, user_profile)
    
    # Get pending actions for each application
    pending_actions = get_pending_actions(user, user_roles, user_profile)
    
    # Get recently actioned items
    recent_actions = get_recent_actions(user, user_profile)
    
    # Get workflow metrics
    workflow_metrics = get_workflow_metrics(user_roles, user_profile)
    
    # Get dashboard widgets
    widgets = get_user_widgets(user_profile)
    
    # Calculate summary metrics
    total_pending = sum(len(items) for items in pending_actions.values())
    total_actioned = sum(app['actioned_count'] for app in accessible_apps.values())
    total_applications = len(accessible_apps)
    
    context = {
        'user_profile': user_profile,
        'accessible_apps': accessible_apps,
        'pending_actions': pending_actions,
        'recent_actions': recent_actions,
        'workflow_metrics': workflow_metrics,
        'user_roles': user_roles,
        'preferences': preferences,
        'widgets': widgets,
        'total_pending': total_pending,
        'total_actioned': total_actioned,
        'total_applications': total_applications,
    }
    
    return render(request, 'general_dashboards/action_dashboard.html', context)


def get_user_applications(user_roles):
    """Get all applications the user has roles for with metrics"""
    apps = {}
    
    app_icons = {
        'ace': 'fas fa-dollar-sign',
        'pettycash': 'fas fa-coins',
        'tokens': 'fas fa-ticket-alt',
        'purchase_request': 'fas fa-shopping-cart',
        'change_requests': 'fas fa-code-branch',
        'safety': 'fas fa-shield-alt',
        'assets': 'fas fa-laptop',
        'transport': 'fas fa-truck',
        'users': 'fas fa-users',
        'knowledge_center': 'fas fa-book',
        'direct_purchase': 'fas fa-file-invoice',
        'comparative_schedule': 'fas fa-chart-bar',
        'restricted_bidding': 'fas fa-gavel',
        'direct_purchases': 'fas fa-shopping-bag',
        'temper': 'fas fa-thermometer-half',
        'clear_credit': 'fas fa-credit-card',
        'virement': 'fas fa-exchange-alt',
        'dashboards': 'fas fa-tachometer-alt',
    }
    
    app_colors = {
        'ace': 'bg-green-500',
        'pettycash': 'bg-blue-500',
        'tokens': 'bg-purple-500',
        'purchase_request': 'bg-orange-500',
        'change_requests': 'bg-indigo-500',
        'safety': 'bg-red-500',
        'assets': 'bg-gray-500',
        'transport': 'bg-yellow-500',
        'users': 'bg-pink-500',
        'knowledge_center': 'bg-teal-500',
        'direct_purchase': 'bg-cyan-500',
        'comparative_schedule': 'bg-lime-500',
        'restricted_bidding': 'bg-amber-500',
        'direct_purchases': 'bg-emerald-500',
        'temper': 'bg-rose-500',
        'clear_credit': 'bg-violet-500',
        'virement': 'bg-sky-500',
        'dashboards': 'bg-slate-500',
    }
    
    for role in user_roles:
        app_name = role.application
        if app_name not in apps:
            apps[app_name] = {
                'name': app_name,
                'roles': [],
                'icon': app_icons.get(app_name, 'fas fa-cog'),
                'color': app_colors.get(app_name, 'bg-gray-500'),
                'pending_count': 0,
                'actioned_count': 0,
                'total_items': 0
            }
        apps[app_name]['roles'].append({
            'role': role.role,
            'name': role.name,
            'description': role.description
        })
    
    return apps


def get_user_applications_with_metrics(user_roles, user_profile):
    """Get applications with detailed metrics"""
    apps = get_user_applications(user_roles)
    
    # Calculate metrics for each application
    for app_name in apps.keys():
        pending_count, actioned_count, total_items = get_application_metrics(app_name, user_roles, user_profile)
        apps[app_name]['pending_count'] = pending_count
        apps[app_name]['actioned_count'] = actioned_count
        apps[app_name]['total_items'] = total_items
        
        # Calculate percentage if there are items
        if total_items > 0:
            apps[app_name]['actioned_percentage'] = round((actioned_count / total_items) * 100, 1)
        else:
            apps[app_name]['actioned_percentage'] = 0
    
    return apps


def get_application_metrics(app_name, user_roles, user_profile):
    """Calculate metrics for a specific application"""
    pending_count = 0
    actioned_count = 0
    total_items = 0
    
    try:
        if app_name == 'ace':
            # ACE metrics
            ace_pending = get_ace_pending_actions(None, user_roles, user_profile)
            pending_count = len(ace_pending)
            
            # Count actioned ACEs (where user has approved/rejected)
            actioned_aces = Approval.objects.filter(
                user=user_profile,
                process__ace2_set__isnull=False
            ).count()
            actioned_count = actioned_aces
            
        elif app_name == 'pettycash':
            # PettyCash metrics
            petty_pending = get_pettycash_pending_actions(None, user_roles, user_profile)
            pending_count = len(petty_pending)
            
            # Count actioned PettyCash items
            actioned_petty = Approval.objects.filter(
                user=user_profile,
                process__pettycash_set__isnull=False
            ).count()
            actioned_count = actioned_petty
            
        elif app_name == 'tokens':
            # Token metrics
            token_pending = get_token_pending_actions(None, user_roles, user_profile)
            pending_count = len(token_pending)
            
            # Count actioned Tokens
            actioned_tokens = Approval.objects.filter(
                user=user_profile,
                process__token_set__isnull=False
            ).count()
            actioned_count = actioned_tokens
            
        elif app_name == 'change_requests':
            # Change Request metrics
            try:
                from it.change_requests.models import ChangeRequest, CRApproval
                # Count pending change requests for user
                pending_crs = ChangeRequest.objects.filter(
                    # Add conditions based on your change request workflow
                    status__in=['pending', 'in_review']
                ).count()
                pending_count = pending_crs
                
                # Count actioned change requests
                actioned_crs = CRApproval.objects.filter(
                    approver=user_profile
                ).count()
                actioned_count = actioned_crs
            except Exception as e:
                print(f"Error calculating change request metrics: {e}")
                
        elif app_name == 'direct_purchase':
            # Direct Purchase metrics
            try:
                from finance.direct_purchase.models import DirectPurchase, DPApproval
                # Count pending direct purchases
                pending_dp = DirectPurchase.objects.filter(
                    # Add conditions based on your workflow
                ).count()
                pending_count = pending_dp
                
                # Count actioned direct purchases
                actioned_dp = DPApproval.objects.filter(
                    user=user_profile
                ).count()
                actioned_count = actioned_dp
            except Exception as e:
                print(f"Error calculating direct purchase metrics: {e}")
                
        elif app_name == 'comparative_schedule':
            # Comparative Schedule metrics
            try:
                from finance.comparative_schedules.models import ComparativeSchedules, CSApproval
                pending_cs = ComparativeSchedules.objects.filter(
                    # Add conditions based on your workflow
                ).count()
                pending_count = pending_cs
                
                actioned_cs = CSApproval.objects.filter(
                    user=user_profile
                ).count()
                actioned_count = actioned_cs
            except Exception as e:
                print(f"Error calculating comparative schedule metrics: {e}")
                
        elif app_name == 'restricted_bidding':
            # Restricted Bidding metrics
            try:
                from finance.ristricted_bidding.models import RistricedBiddings, RBApproval
                pending_rb = RistricedBiddings.objects.filter(
                    # Add conditions based on your workflow
                ).count()
                pending_count = pending_rb
                
                actioned_rb = RBApproval.objects.filter(
                    user=user_profile
                ).count()
                actioned_count = actioned_rb
            except Exception as e:
                print(f"Error calculating restricted bidding metrics: {e}")
                
        elif app_name == 'safety':
            # Safety metrics
            try:
                from safety.models import SafetyMonthlyReport
                # Count pending safety reports that need review
                pending_safety = SafetyMonthlyReport.objects.filter(
                    # Add conditions for reports pending review
                ).count()
                pending_count = pending_safety
                
                # Count safety reports the user has worked on
                actioned_safety = SafetyMonthlyReport.objects.filter(
                    user=user_profile
                ).count()
                actioned_count = actioned_safety
            except Exception as e:
                print(f"Error calculating safety metrics: {e}")
                
        total_items = pending_count + actioned_count
        
    except Exception as e:
        print(f"Error calculating metrics for {app_name}: {e}")
    
    return pending_count, actioned_count, total_items


def get_pending_actions(user, user_roles, user_profile):
    """Get all pending items requiring user action across all applications"""
    pending_items = {
        'urgent': [],
        'high': [],
        'medium': [],
        'low': []
    }
    
    # ACE Approvals
    ace_pending = get_ace_pending_actions(user, user_roles, user_profile)
    
    # PettyCash Approvals
    petty_pending = get_pettycash_pending_actions(user, user_roles, user_profile)
    
    # Token Approvals
    token_pending = get_token_pending_actions(user, user_roles, user_profile)
    
    # Purchase Request Approvals
    pr_pending = get_purchase_request_pending_actions(user, user_roles, user_profile)
    
    # Change Request Approvals
    cr_pending = get_change_request_pending_actions(user, user_roles, user_profile)
    
    # Safety Report Reviews
    safety_pending = get_safety_pending_actions(user, user_roles, user_profile)
    
    # Asset Management Actions
    asset_pending = get_asset_pending_actions(user, user_roles, user_profile)
    
    # Categorize by priority
    all_pending = [
        *ace_pending, *petty_pending, *token_pending, 
        *pr_pending, *cr_pending, *safety_pending, *asset_pending
    ]
    
    for item in all_pending:
        priority = calculate_priority(item)
        pending_items[priority].append(item)
    
    return pending_items


def get_ace_pending_actions(user, user_roles, user_profile):
    """Get pending ACE items for approval"""
    pending_aces = []
    region = user_profile.region
    
    if not region:
        return pending_aces
    
    # Get ACEs where user is next approver
    try:
        for ace in Ace2.objects.filter(region=region):
            process = ace.process
            if not process:
                continue
                
            # Skip rejected items
            if process.approval_set.filter(approved="Rejected").exists():
                continue
                
            # Get next step
            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                next_step = last_approval.step.step + 1
            else:
                next_step = 1
                
            # Check if user is next approver
            try:
                step = Step.objects.get(
                    step=next_step, 
                    workflow=process.workflow, 
                    approver__in=user_roles
                )
                
                days_pending = (timezone.now().date() - ace.date_created).days if ace.date_created else 0
                
                pending_aces.append({
                    'type': 'ACE',
                    'id': ace.Ace_id2,
                    'title': f"ACE {ace.Ace_id2}",
                    'description': ace.details_of_expenditure or 'No description',
                    'amount': ace.amount or 0,
                    'requester': ace.requested_by or 'Unknown',
                    'date_created': ace.date_created,
                    'current_step': next_step,
                    'days_pending': days_pending,
                    'url': reverse('Ace:ace_detail', args=[ace.Ace_id2]),
                    'action_required': step.approver.name,
                    'urgency': get_urgency_level(ace.amount or 0, ace.date_created)
                })
            except Step.DoesNotExist:
                continue
    except Exception as e:
        print(f"Error getting ACE pending actions: {e}")
            
    return pending_aces


def get_pettycash_pending_actions(user, user_roles, user_profile):
    """Get pending PettyCash items for approval"""
    pending_petty = []
    region = user_profile.region
    
    if not region:
        return pending_petty
    
    try:
        for petty in Pettycash.objects.filter(region=region):
            process = petty.process
            if not process:
                continue
                
            # Skip rejected items
            if process.approval_set.filter(approved="Rejected").exists():
                continue
                
            # Get next step
            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                next_step = last_approval.step.step + 1
            else:
                next_step = 1
                
            # Check if user is next approver
            try:
                step = Step.objects.get(
                    step=next_step, 
                    workflow=process.workflow, 
                    approver__in=user_roles
                )
                
                days_pending = (timezone.now().date() - petty.date_created).days if petty.date_created else 0
                
                pending_petty.append({
                    'type': 'PettyCash',
                    'id': petty.petty_id,
                    'title': f"Petty Cash {petty.petty_id}",
                    'description': petty.description or 'No description',
                    'amount': petty.amount or 0,
                    'requester': petty.requested_by.get_full_name() if petty.requested_by else 'Unknown',
                    'date_created': petty.date_created,
                    'current_step': next_step,
                    'days_pending': days_pending,
                    'url': reverse('pettycash:pettycash_detail', args=[petty.petty_id]),
                    'action_required': step.approver.name,
                    'urgency': get_urgency_level(petty.amount or 0, petty.date_created)
                })
            except Step.DoesNotExist:
                continue
    except Exception as e:
        print(f"Error getting PettyCash pending actions: {e}")
            
    return pending_petty


def get_token_pending_actions(user, user_roles, user_profile):
    """Get pending Token items for approval"""
    pending_tokens = []
    
    try:
        for token in Token.objects.all():
            process = token.process
            if not process:
                continue
                
            # Skip rejected items
            if process.approval_set.filter(approved="Rejected").exists():
                continue
                
            # Get next step
            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                next_step = last_approval.step.step + 1
            else:
                next_step = 1
                
            # Check if user is next approver
            try:
                step = Step.objects.get(
                    step=next_step, 
                    workflow=process.workflow, 
                    approver__in=user_roles
                )
                
                days_pending = (timezone.now().date() - token.created_at.date()).days if token.created_at else 0
                
                pending_tokens.append({
                    'type': 'Token',
                    'id': token.id,
                    'title': f"Token {token.id}",
                    'description': token.reason or 'No description',
                    'amount': 0,  # Tokens don't have amounts
                    'requester': token.created_by.get_full_name() if token.created_by else 'Unknown',
                    'date_created': token.created_at.date() if token.created_at else None,
                    'current_step': next_step,
                    'days_pending': days_pending,
                    'url': reverse('tokens:token', args=[token.id]),
                    'action_required': step.approver.name,
                    'urgency': get_urgency_level(0, token.created_at.date() if token.created_at else None)
                })
            except Step.DoesNotExist:
                continue
    except Exception as e:
        print(f"Error getting Token pending actions: {e}")
            
    return pending_tokens


def get_purchase_request_pending_actions(user, user_roles, user_profile):
    """Get pending Purchase Request items"""
    # Implementation depends on your purchase request workflow
    return []


def get_change_request_pending_actions(user, user_roles, user_profile):
    """Get pending Change Request items"""
    # Implementation for change requests
    return []


def get_safety_pending_actions(user, user_roles, user_profile):
    """Get pending Safety items"""
    # Implementation for safety reports
    return []


def get_asset_pending_actions(user, user_roles, user_profile):
    """Get pending Asset Management items"""
    # Implementation for asset management
    return []


def get_recent_actions(user, user_profile):
    """Get recently actioned items by the user"""
    recent_actions = []
    
    try:
        # Get recent approvals
        recent_approvals = Approval.objects.filter(
            user=user_profile
        ).order_by('-approved_at')[:10]
        
        for approval in recent_approvals:
            process = approval.process
            item_title = "Unknown Item"
            item_url = "#"
            
            # Determine the item type and get details
            if hasattr(process, 'ace2_set') and process.ace2_set.exists():
                ace = process.ace2_set.last()
                item_title = f"ACE {ace.Ace_id2}"
                item_url = reverse('Ace:ace_detail', args=[ace.Ace_id2])
            elif hasattr(process, 'pettycash_set') and process.pettycash_set.exists():
                petty = process.pettycash_set.last()
                item_title = f"Petty Cash {petty.petty_id}"
                item_url = reverse('pettycash:pettycash_detail', args=[petty.petty_id])
            elif hasattr(process, 'token_set') and process.token_set.exists():
                token = process.token_set.last()
                item_title = f"Token {token.id}"
                item_url = reverse('tokens:token', args=[token.id])
            
            recent_actions.append({
                'title': item_title,
                'action': approval.approved,
                'date': approval.approved_at,
                'url': item_url,
                'status_color': 'bg-green-500' if approval.approved == 'Approved' else 'bg-red-500'
            })
    except Exception as e:
        print(f"Error getting recent actions: {e}")
    
    return recent_actions


def get_workflow_metrics(user_roles, user_profile):
    """Get workflow performance metrics"""
    metrics = {
        'total_pending': 0,
        'avg_approval_time': 0,
        'approval_rate': 0,
        'workload_distribution': {}
    }
    
    try:
        # Calculate metrics for different workflow types
        workflows = ['ace', 'pettycash', 'tokens', 'purchase_request']
        
        for workflow_name in workflows:
            try:
                workflow = Workflow.objects.get(name=workflow_name)
                
                # Count pending items for this workflow
                pending_count = Process.objects.filter(
                    workflow=workflow,
                    approval_set__step__approver__in=user_roles
                ).exclude(
                    approval_set__approved="Rejected"
                ).count()
                
                metrics['workload_distribution'][workflow_name] = {
                    'pending_count': pending_count,
                    'name': workflow_name.title()
                }
                
                metrics['total_pending'] += pending_count
                
            except Workflow.DoesNotExist:
                metrics['workload_distribution'][workflow_name] = {
                    'pending_count': 0,
                    'name': workflow_name.title()
                }
    except Exception as e:
        print(f"Error calculating workflow metrics: {e}")
    
    return metrics


def get_user_widgets(user_profile):
    """Get dashboard widgets for the user based on their roles"""
    # Implementation for dashboard widgets
    return []


def calculate_priority(item):
    """Calculate priority based on amount, age, and type"""
    days_pending = item.get('days_pending', 0)
    amount = item.get('amount', 0)
    item_type = item.get('type', '')
    
    # Urgent: High amount + old + critical type
    if (amount > 100000 and days_pending > 7) or days_pending > 14:
        return 'urgent'
    elif amount > 50000 or days_pending > 5:
        return 'high'
    elif amount > 10000 or days_pending > 3:
        return 'medium'
    else:
        return 'low'


def get_urgency_level(amount, date_created):
    """Get urgency level for an item"""
    if not date_created:
        return 'medium'
    
    days_old = (timezone.now().date() - date_created).days
    
    if amount > 100000 or days_old > 14:
        return 'urgent'
    elif amount > 50000 or days_old > 7:
        return 'high'
    elif amount > 10000 or days_old > 3:
        return 'medium'
    else:
        return 'low'


@login_required
def dashboard_api(request):
    """API endpoint for dashboard data"""
    user = request.user
    user_profile = get_object_or_404(UserProfile, id=user.id)
    user_roles = user_profile.roles.all()
    
    # Get data based on request parameters
    data_type = request.GET.get('type', 'all')
    
    if data_type == 'pending_actions':
        pending_actions = get_pending_actions(user, user_roles, user_profile)
        return JsonResponse(pending_actions)
    elif data_type == 'workflow_metrics':
        metrics = get_workflow_metrics(user_roles, user_profile)
        return JsonResponse(metrics)
    elif data_type == 'recent_actions':
        recent_actions = get_recent_actions(user, user_profile)
        return JsonResponse({'recent_actions': recent_actions})
    
    return JsonResponse({'error': 'Invalid data type'}, status=400)


@login_required
def update_preferences(request):
    """Update user dashboard preferences"""
    if request.method == 'POST':
        user_profile = get_object_or_404(UserProfile, id=request.user.id)
        preferences, created = DashboardPreference.objects.get_or_create(user=user_profile)
        
        # Update preferences from form data
        preferences.default_priority_filter = request.POST.get('priority_filter', 'all')
        preferences.items_per_page = int(request.POST.get('items_per_page', 10))
        preferences.show_completed_actions = request.POST.get('show_completed') == 'on'
        preferences.email_notifications = request.POST.get('email_notifications') == 'on'
        
        preferences.save()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# =================== NEW DASHBOARD DATA API VIEWS ===================

@csrf_exempt
@require_http_methods(["GET"])
def get_regions(request):
    """Get all regions, districts, sections, and depots for filters"""
    from it.users.models import Regions, Districts, Sections, Depots
    
    regions = list(Regions.objects.values('id', 'region'))
    districts = list(Districts.objects.values('id', 'district', 'region_id'))
    sections = list(Sections.objects.values('id', 'section', 'district_id', 'region_id'))
    depots = list(Depots.objects.values('id', 'depot', 'district_id', 'region_id'))
    
    # Get sample data for compatibility
    pbncs = []  # Add your PBNC data logic here
    upos = []   # Add your UPO data logic here
    weekly_sales = list(WeeklySales.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'zwl', 'usd'))
    
    weekly_outages = list(WeeklyOutage.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'outages', 'resolved', 'pending'))
    
    tds = list(TopDebtor.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('name', 'amount'))
    
    weekly_faults_maintenance = list(WeeklyFaultMaintenance.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'faults', 'maintenance', 'completed', 'pending'))
    
    return JsonResponse({
        'regions': regions,
        'districts': districts,
        'sections': sections,
        'depots': depots,
        'pbncs': pbncs,
        'weekly_sales': weekly_sales,
        'upos': upos,
        'weekly_outages': weekly_outages,
        'tds': tds,
        'weekly_faults_maintenance': weekly_faults_maintenance,
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_dashboard_data(request):
    """Get initial dashboard data"""
    # Get metrics
    metrics = {}
    for metric in DashboardMetric.objects.filter(region__isnull=True, district__isnull=True, depot__isnull=True):
        metrics[metric.metric_type] = {
            'value': metric.value,
            'unit': metric.unit,
            'target': metric.target,
            'target_unit': metric.target_unit,
            'progress': metric.progress
        }
    
    # Get chart data (mock for now)
    inspection_locations = json.dumps(['Location A', 'Location B', 'Location C'])
    inspections_count = json.dumps([10, 15, 8])
    maintenance_locations = json.dumps(['Site 1', 'Site 2', 'Site 3'])
    maintenance_count = json.dumps([5, 12, 7])
    mtn = {'Site 1': [1, 2, 3, 4], 'Site 2': [2, 3, 1, 5]}
    
    # Get table data
    weekly_sales = list(WeeklySales.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'zwl', 'usd'))
    
    weekly_outages = list(WeeklyOutage.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'outages', 'resolved', 'pending'))
    
    weekly_faults_maintenance = list(WeeklyFaultMaintenance.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'faults', 'maintenance', 'completed', 'pending'))
    
    tds = list(TopDebtor.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('name', 'amount'))
    
    return JsonResponse({
        'metrics': metrics,
        'inspection_locations': inspection_locations,
        'inspections_count': inspections_count,
        'maintenance_locations': maintenance_locations,
        'maintenance_count': maintenance_count,
        'mtn': mtn,
        'pbncs': [],
        'weekly_sales': weekly_sales,
        'upos': [],
        'weekly_outages': weekly_outages,
        'tds': tds,
        'weekly_faults_maintenance': weekly_faults_maintenance,
    })


@csrf_exempt
@require_http_methods(["POST"])
def dashboard_filter(request):
    """Filter dashboard data by location"""
    data = json.loads(request.body)
    region_id = data.get('region')
    district_id = data.get('district')
    depot_id = data.get('depot')
    
    # Build filter conditions
    filter_kwargs = {}
    if depot_id:
        filter_kwargs['depot_id'] = depot_id
    elif district_id:
        filter_kwargs['district_id'] = district_id
    elif region_id:
        filter_kwargs['region_id'] = region_id
    
    # Get filtered data
    weekly_sales = list(WeeklySales.objects.filter(**filter_kwargs).values('week', 'zwl', 'usd'))
    weekly_outages = list(WeeklyOutage.objects.filter(**filter_kwargs).values('week', 'outages', 'resolved', 'pending'))
    weekly_faults_maintenance = list(WeeklyFaultMaintenance.objects.filter(**filter_kwargs).values('week', 'faults', 'maintenance', 'completed', 'pending'))
    tds = list(TopDebtor.objects.filter(**filter_kwargs).values('name', 'amount'))
    
    # Mock chart data for now
    inspection_locations = json.dumps(['Filtered Location A', 'Filtered Location B'])
    inspections_count = json.dumps([5, 8])
    maintenance_locations = json.dumps(['Filtered Site 1', 'Filtered Site 2'])
    maintenance_count = json.dumps([3, 9])
    mtn = {'Filtered Site 1': [1, 2, 1, 3], 'Filtered Site 2': [2, 1, 2, 4]}
    
    return JsonResponse({
        'inspection_locations': inspection_locations,
        'inspections_count': inspections_count,
        'maintenance_locations': maintenance_locations,
        'maintenance_count': maintenance_count,
        'mtn': mtn,
        'pbncs': [],
        'weekly_sales': weekly_sales,
        'upos': [],
        'weekly_outages': weekly_outages,
        'tds': tds,
        'weekly_faults_maintenance': weekly_faults_maintenance,
    })


@csrf_exempt
@require_http_methods(["POST"])
def save_dashboard_data(request):
    """Save edited dashboard data"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        data = json.loads(request.body)
        table = data.get('table')
        row = data.get('row')
        field = data.get('field')
        value = data.get('value')
        
        if table == 'metrics':
            # Handle metric updates
            metric_key = row  # row contains the metric key
            property_name = field  # field contains the property name
            
            metric, created = DashboardMetric.objects.get_or_create(
                metric_type=metric_key,
                region__isnull=True,
                district__isnull=True,
                depot__isnull=True,
                defaults={'value': '0', 'unit': '', 'target': '0', 'target_unit': '', 'progress': 0}
            )
            
            setattr(metric, property_name, value)
            metric.updated_by = request.user
            metric.save()
            
        elif table == 'weekly_sales':
            # Handle weekly sales updates
            sales_items = list(WeeklySales.objects.filter(
                region__isnull=True, district__isnull=True, depot__isnull=True
            ).order_by('week_number'))
            
            if row < len(sales_items):
                sales_item = sales_items[row]
                setattr(sales_item, field, value)
                sales_item.save()
                
        elif table == 'weekly_outages':
            # Handle weekly outages updates
            outage_items = list(WeeklyOutage.objects.filter(
                region__isnull=True, district__isnull=True, depot__isnull=True
            ).order_by('week_number'))
            
            if row < len(outage_items):
                outage_item = outage_items[row]
                setattr(outage_item, field, int(value) if field in ['outages', 'resolved', 'pending'] else value)
                outage_item.save()
                
        elif table == 'weekly_faults_maintenance':
            # Handle weekly faults/maintenance updates
            fault_items = list(WeeklyFaultMaintenance.objects.filter(
                region__isnull=True, district__isnull=True, depot__isnull=True
            ).order_by('week_number'))
            
            if row < len(fault_items):
                fault_item = fault_items[row]
                setattr(fault_item, field, int(value) if field in ['faults', 'maintenance', 'completed', 'pending'] else value)
                fault_item.save()
                
        elif table == 'tds':
            # Handle top debtors updates
            debtor_items = list(TopDebtor.objects.filter(
                region__isnull=True, district__isnull=True, depot__isnull=True
            ).order_by('rank'))
            
            if row < len(debtor_items):
                debtor_item = debtor_items[row]
                setattr(debtor_item, field, value)
                debtor_item.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
