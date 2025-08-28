import csv
import random
from datetime import datetime, timedelta
import json
import simplejson as jsons
from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from executive.exec_dashboards.utils import *
from .models import PBNC, TD, UPO, Inspections, Maintenance
from django.core import serializers
from django.db.models import Count
from django.db.models.functions import ExtractWeek
from django.db.models import Q  # Import Q object for complex filtering
from django.contrib.auth.decorators import login_required

from it.users.models import Sections, UserProfile, Depots, Districts, Regions
from executive.general_dashboards.models import DashboardMetric, WeeklySales, WeeklyOutage, WeeklyFaultMaintenance, TopDebtor, WeeklyCollections, WeeklyRevenueLost, DebtorCategory

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# Create your views here.
def get_random_date(start_date, end_date):
    """
    Returns a random date between start_date and end_date (inclusive).
    """
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")


def setup_random_data(request):
    regions_ = Regions.objects.all()
    districts_ = Districts.objects.all()
    depots_ = Depots.objects.all()
    locations = [
        "Alex Park - Part",
        "Alex Park - Part",
        "Amalinda",
        "Amalinda Farm",
        "Ambleside",
        "Amby",
        "Arbour Cres",
        "Art Farm",
        "Ashbritle",
        "Ashdown Park",
        "Athlone",
        "Athlone - Part",
        "Avenues",
        "Avondale",
        "Avondale West",
        "Avonlea - Part",
        "Avonlea West",
        "Ballantyne Park",
        "Bannockburn",
        "Barrington Rd Area",
        "Belgravia",
        "Belvedere",
        "Borrowdale",
        "Borrowdale Brook",
        "Borrowdale N",
        "Bothashof",
        "Budiriro",
        "Carrick",
        "Chadcombe",
        "Chedgelow",
        "Chikurubi",
        "Chiltern Hill",
        "Chishawasha",
        "Chishawasha",
        "Chisipite",
        "Colne Valley",
        "Colne Valley",
        "Colray",
        "Colray",
        "Coronation Park",
        "Glen Norah",
        "Glen Norah A - Part",
        "Glen Wood",
        "Glenview",
        "Glenview - Part",
        "Greendale - Part",
        "Greendale - Part",
        "Greendale - Part",
        "Greendcroft",
        "Greengrove",
        "Greystone Park",
        "Grobbie Park",
        "Groombridge",
        "Guildform Estate",
        "Gunhill",
        "Haig Park",
        "Harare Rd W",
        "Harava Dam",
        "Hatcliffe",
        "Hatfield West",
        "Hat-Twentydales -Part",
        "Hatlands Farm",
        "Helensvale",
        "Helensvale S",
        "Highfield",
        "Highlands - Part",
        "Highlands - Part",
        "Highlands - Part",
        "Hillside",
        "Hopley",
        "Hunyani Poort",
        "Induna",
        "Ingwe Farm",
        "Jerusalem",
        "Kambuzuma",
        "Kambuzuma",
        "Kambuzuma South",
        "Kensington",
        "Kensington",
        "Kingsmead",
        "Mabvuku",
        "Machipisa",
        "Malvern",
        "Mandalay Park",
        "Mandara",
        "Marimba Park",
        "Marlborough",
        "Mayfield Park",
        "Mbare",
        "Merwede",
        "Meyrick Park",
        "Midlands",
        "Milton Park",
        "Monavale",
        "Msasa Park",
        "Mt Pleasant & Heights",
        "Mt Hampden",
        "Matidoda",
        "Mufakose",
        "Mutare Rd",
        "Newlands",
        "Newlands East",
        "Northwood",
        "Old Highfields",
        "Pangula",
        "Paradise Park",
        "Park Meadowlands",
        "Parkridge",
        "Parkridge Estate",
        "Parktown",
        "Pension Farm",
        "Pension Farm",
        "Pomona",
        "Prospect East",
        "Prospect West",
        "Queensdale",
        "Quinnington",
        "Quinnington S",
        "Rambabvu",
        "Reiforntein",
        "Sherwood Park - Part",
        "Somerby Area",
        "Spring Heights",
        "Stanbury Park",
        "Startmore Farm",
        "Stoneridge Rd",
        "Strathaven",
        "Sunridge",
        "Tafara",
        "The Grange",
        "Thornpark",
        "Twentydales Ext.",
        "Tynwald North",
        "Tynwald South",
        "Umwinsidale",
        "Uplands",
        "Upper Mt Hampden",
        "Upper Reaches Rd",
        "Vainona",
        "Valencedene",
        "Waldon Area",
        "Warren Park",
        "Warren Park - Part",
        "Warren Park - Part",
        "Warren Park E",
        "Waterfalls",
        "Westlea",
        "Westwood",
        "Widdecombe",
        "Wilmington Park",
        "Winchdon",
        "Southlea Park",
        "Rydale Ridge",
        "Whitecliffe",
        "Southerton Residential",
        "Cotswold Hills",
        "Cranborne Park",
        "Creagh",
        "Crowborough",
        "Crowborough Estate",
        "Crowhill",
        "Draycot",
        "Dzivaresekwa",
        "Eastlea",
        "Eastlea",
        "Emerald Hill",
        "Epworth",
        "Getwyn",
        "Glen Lorne",
        "Glen Lorne West",
        "Zengeza 1, 2,3, 4 & 5",
        "Zengeza 5 Ext",
        "Guzha",
        "Unit J",
        "St Mary's",
        "Manyame Park",
        "Kintyre",
        "Komani",
        "Kutsaga",
        "Kuwadzana",
        "Lake Chivero",
        "Langford Farm",
        "Lewisam",
        "Lincoln Green",
        "Little Norfolk",
        "Logan Park",
        "Lonchinvar",
        "Luna",
        "Lusaka",
        "Mabelreign",
        "Mabelreign N",
        "Reiforntein - Part",
        "Rhodesville",
        "Ridgeview",
        "Rolf Valley South",
        "Rolf Valley N",
        "Ruwa",
        "Ruwa",
        "S Mazorodze Areas",
        "Safron Area",
        "San Souci Rd Area",
        "San Souci Rd Area",
        "Seki Rd Area",
        "Seki Rd N",
        "Sentosa",
        "Sherwood Park - Part",
        "Seke Unit A, B, C, D, E",
        "Seke Unit F, G Old",
        "Seke Unit K, L, M",
        "Town Centre",
        "Seke Unit B, Makoni",
        "Seke Unit M,N, O, P",
        "Police Flats, Unit B",
        "Murisa T/Ship, Dema",
        "Manyame Park",
        "St Mary's",
        "Mayambara",
        "GDC",
        "Jaggers, Chibuku, DMB",
        "Southern Granite",
        "Sewage Works",
        "Surface Investments",
        "Parts of Unit K",
        "22 Miles",
        "3 Brigade",
        "3-2 Battalion",
        "4 Brigade",
        "Adams Barracks",
        "Africa University",
        "All of Masvingo Province",
        "Anderson school",
        "Arda Transau",
        "Avila",
        "Bangala",
        "Bangazani Dam",
        "Bannockburn",
        "Bende",
        "Bikita",
        "Bikita Minerals",
        "Bikita Village",
        "Birchenough Bridge",
        "Birthday Mine",
        "BNR",
        "Bonda",
        "Bonda Irrigation",
        "Bordervale",
        "Buffalo Range",
        "Buhera",
        "Bumba",
        "Burma Valley"
    ]

    depots = depots_.values_list("depot", flat=True)
    districts = districts_.values_list("district", flat=True)
    regions = regions_.values_list("region", flat=True)
    data = []

    for _ in range(1000):
        location = random.choice(locations)
        depot = random.choice(depots)
        district = random.choice(districts)
        region = random.choice(regions)
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 30)
        random_date = get_random_date(start_date, end_date)
        created_at = random_date
        
        data.append([location, depot, district, region, created_at])

    # Save the data as a CSV file
    filename = "inspection_data.csv"
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["location", "depot", "district", "region", "created_at"])  # Write header
        writer.writerows(data)

    print(f"Data has been saved as {filename}")

def get_regions(request):
    from executive.general_dashboards.models import (
        WeeklyCollections, WeeklyRevenueLost, DebtorCategory,
        WeeklySales, WeeklyOutage, WeeklyFaultMaintenance, TopDebtor
    )
    
    regions = Regions.objects.all()
    districts = Districts.objects.all()
    sections = Sections.objects.all()
    depots = Depots.objects.all()
    
    # Get sample data for compatibility
    pbncs = []  # Add your PBNC data logic here
    upos = []   # Add your UPO data logic here
    
    # Legacy data (for backward compatibility)
    weekly_sales = list(WeeklySales.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'zwl', 'usd'))
    
    weekly_outages = list(WeeklyOutage.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'outages', 'resolved', 'pending'))
    
    # tds = list(TopDebtor.objects.filter(
    #     region__isnull=True, district__isnull=True, depot__isnull=True
    # ).values('name', 'amount'))
    tds = []  # Temporary fix for database schema issue
    
    weekly_faults_maintenance = list(WeeklyFaultMaintenance.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'faults', 'maintenance', 'completed', 'pending'))
    
    # New data sections (default to global data)
    default_location_filter = {'region__isnull': True, 'district__isnull': True, 'depot__isnull': True}
    
    weekly_collections = list(WeeklyCollections.objects.filter(
        **default_location_filter
    ).values('week', 'zwl_millions', 'usd_millions'))
    
    weekly_revenue_lost = list(WeeklyRevenueLost.objects.filter(
        **default_location_filter
    ).values('week', 'faults_mwh', 'maintenance_mwh', 'total_mwh'))
    
    debtors = list(DebtorCategory.objects.filter(
        **default_location_filter
    ).values('id', 'category', 'percentage'))
    
    return JsonResponse({
        'regions': list(regions.values('id', 'region')),
        'districts': list(districts.values('id', 'district', 'region_id')),
        'sections': list(sections.values('id', 'section', 'district_id', 'region_id')),
        'depots': list(depots.values('id', 'depot', 'district_id', 'region_id')),
        'pbncs': pbncs,
        'weekly_sales': weekly_sales,
        'upos': upos,
        'weekly_outages': weekly_outages,
        'tds': tds,
        'weekly_faults_maintenance': weekly_faults_maintenance,
        # New data sections
        'weekly_collections': weekly_collections,
        'weekly_revenue_lost': weekly_revenue_lost,
        'debtors': debtors,
    })

def get_districts(request):
    districts = Districts.objects.all()
    return JsonResponse(list(districts.values('id', 'district')), safe=False)

@login_required
def dashboard_data(request):
    
    user = request.user
    user_profile = UserProfile.objects.filter(id=user.id).first()

    # fetch pbnc data
    pbncs = PBNC.objects.all().order_by('-amount')
    tds = TD.objects.all().order_by('-amount')
    upos = UPO.objects.all()
    
    month_id = datetime.now().month
    mtn = get_mmt(user_profile, month_id)
    
    keys_list, values_list = get_inspections_bargraph(user_profile, month_id)

    inspection_locations = json.dumps(keys_list)
    inspections_count = json.dumps(values_list)
    
    # loop through maintences and foreach get record count from Files.
    maintenance_keys_list, maintenance_values_list = get_maintenance_linegraph(user_profile, month_id)
    print("mmt: ", maintenance_keys_list, maintenance_values_list)

    # Get metrics from our new models
    metrics = {}
    for metric in DashboardMetric.objects.filter(region__isnull=True, district__isnull=True, depot__isnull=True):
        metrics[metric.metric_type] = {
            'value': metric.value,
            'unit': metric.unit,
            'target': metric.target,
            'target_unit': metric.target_unit,
            'progress': metric.progress
        }

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
    
    # Get new top debtors data
    top_debtors = list(TopDebtor.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('name', 'amount'))

    # Get new data sections
    weekly_collections = list(WeeklyCollections.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'zwl_millions', 'usd_millions'))
    
    weekly_revenue_lost = list(WeeklyRevenueLost.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('week', 'faults_mwh', 'maintenance_mwh', 'total_mwh'))
    
    debtors = list(DebtorCategory.objects.filter(
        region__isnull=True, district__isnull=True, depot__isnull=True
    ).values('id', 'category', 'percentage'))

    data = {
            "pbncs": list(pbncs.values('id', 'name', 'amount', 'depot', 'district', 'region', 'created_at')),
            "tds": top_debtors,  # Use new TopDebtor data instead of old TD data
            "upos": list(upos.values('id', 'description', 'depot', 'district', 'region', 'created_at')),
            "inspection_locations": inspection_locations, 
            "inspections_count": inspections_count,
            "mtn": mtn, 
            "maintenance_count": maintenance_values_list, 
            "maintenance_locations": maintenance_keys_list,
            "metrics": metrics,
            "weekly_sales": weekly_sales,
            "weekly_outages": weekly_outages,
            "weekly_faults_maintenance": weekly_faults_maintenance,
            "weekly_collections": weekly_collections,
            "weekly_revenue_lost": weekly_revenue_lost,
            "debtors": debtors,
        }

    return JsonResponse(data, safe=False)

@csrf_exempt
def save_dashboard_data(request):
    """Save edited dashboard data"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    # Check if user has permission to edit dashboard data
    try:
        user_role = request.user.get_user_role_for_application("general_dashboards")
        can_edit = user_role and user_role.role == 'maintain'
    except AttributeError:
        # Fallback: check if user is superuser or staff
        can_edit = request.user.is_superuser or request.user.is_staff
    
    if not can_edit:
        return JsonResponse({'success': False, 'error': 'Insufficient permissions to edit dashboard data'})
    
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

@csrf_exempt
@require_http_methods(["GET"])
def user_permissions(request):
    """Get user permissions for dashboard editing"""
    try:
        user = request.user
        user_profile = UserProfile.objects.filter(id=user.id).first()
        
        print(f"DEBUG: Checking permissions for user: {user.username} (ID: {user.id})")
        
        # Check if user has the 'maintain' role for 'general_dashboards' application
        can_edit = False
        user_roles = []
        
        try:
            # Debug: Check if application exists
            from it.users.models import Application
            app = Application.objects.filter(name="general_dashboards").first()
            print(f"DEBUG: Application 'general_dashboards' exists: {app}")
            if app:
                print(f"DEBUG: Application ID: {app.id}, Name: {app.name}, Fullname: {app.fullname}")
            
            # Debug: Check user's roles
            all_user_roles = user_profile.roles.all()
            print(f"DEBUG: User's all roles: {list(all_user_roles.values('id', 'role', 'name', 'application', 'app_id'))}")
            
            # Get the user's role for the general_dashboards application
            user_role = user.get_user_role_for_application("general_dashboards")
            print(f"DEBUG: User role for general_dashboards: {user_role}")
            
            if user_role:
                print(f"DEBUG: Role details - role: {user_role.role}, name: {user_role.name}")
                if user_role.role == 'maintain':
                    can_edit = True
                user_roles = [user_role.name]
            else:
                print("DEBUG: No role found for general_dashboards application")
                
        except AttributeError as e:
            print(f"DEBUG: AttributeError in role checking: {e}")
            # Fallback: check if user is superuser or staff
            can_edit = user.is_superuser or user.is_staff
            user_roles = ['superuser'] if user.is_superuser else (['staff'] if user.is_staff else [])
            print(f"DEBUG: Using fallback - can_edit: {can_edit}, user_roles: {user_roles}")
        
        print(f"DEBUG: Final result - can_edit: {can_edit}, user_roles: {user_roles}")
        
        return JsonResponse({
            'canEdit': can_edit,
            'userRoles': user_roles,
            'user': {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        })
    except Exception as e:
        print(f"Error in user_permissions: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'canEdit': False,
            'userRoles': [],
            'user': {},
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["GET"])
def debug_user_roles(request):
    """Debug endpoint to check user roles and applications"""
    try:
        user = request.user
        user_profile = UserProfile.objects.filter(id=user.id).first()
        
        # Get all applications
        from it.users.models import Application
        all_apps = list(Application.objects.all().values('id', 'name', 'fullname'))
        
        # Get all user roles
        all_user_roles = list(user_profile.roles.all().values('id', 'role', 'name', 'description', 'application', 'app_id'))
        
        # Check for general_dashboards specifically
        general_dashboards_app = Application.objects.filter(name="general_dashboards").first()
        
        debug_info = {
            'user_info': {
                'username': user.username,
                'id': user.id,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            },
            'all_applications': all_apps,
            'user_roles': all_user_roles,
            'general_dashboards_app': {
                'exists': bool(general_dashboards_app),
                'id': general_dashboards_app.id if general_dashboards_app else None,
                'name': general_dashboards_app.name if general_dashboards_app else None,
                'fullname': general_dashboards_app.fullname if general_dashboards_app else None
            } if general_dashboards_app else {'exists': False},
            'role_check_result': None
        }
        
        # Test the role checking method
        try:
            user_role = user.get_user_role_for_application("general_dashboards")
            debug_info['role_check_result'] = {
                'found_role': bool(user_role),
                'role_details': {
                    'role': user_role.role,
                    'name': user_role.name,
                    'app_id': user_role.app_id.id if user_role.app_id else None
                } if user_role else None
            }
        except Exception as e:
            debug_info['role_check_result'] = {
                'error': str(e)
            }
        
        return JsonResponse(debug_info, indent=2)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'traceback': str(e.__traceback__)
        })

@login_required
def dashboard_filters(request):
    
    data = json.loads(request.body)
    selected_region = data.get('region', None)
    selected_district = data.get('district', None)
    selected_depot = data.get('depot', None)
    
    user = request.user
    user_profile = UserProfile.objects.filter(id=user.id).first()

    # fetch pbnc data
    pbncs = PBNC.objects.all().order_by('-amount')
    tds = TD.objects.all().order_by('-amount')
    upos = UPO.objects.all()
    
    month_id = datetime.now().month
    mtn = get_mmt_filter(selected_region, selected_district, selected_depot, month_id, user_profile)
    
    keys_list, values_list = get_inspections_bargraph_filter(selected_region, selected_district, selected_depot, month_id, user_profile)

    inspection_locations = keys_list
    inspections_count = values_list
    print("inspections_count: ", inspections_count)
    
    # loop through maintences and foreach get record count from Files.
    maintenance_keys_list, maintenance_values_list = get_maintenance_linegraph_filter(selected_region, selected_district, selected_depot, month_id, user_profile)
    # print("mmt: ", maintenance_keys_list, maintenance_values_list)

    # Build filter conditions for TopDebtor
    filter_kwargs = {}
    if selected_depot:
        filter_kwargs['depot_id'] = selected_depot
    elif selected_district:
        filter_kwargs['district_id'] = selected_district
    elif selected_region:
        filter_kwargs['region_id'] = selected_region
    else:
        # Default to global data when no location is selected
        filter_kwargs = {'region__isnull': True, 'district__isnull': True, 'depot__isnull': True}
    
    # Get filtered top debtors data
    filtered_top_debtors = list(TopDebtor.objects.filter(**filter_kwargs).values('name', 'amount'))

    data = {
            "pbncs": list(pbncs.values('id', 'name', 'amount', 'depot', 'district', 'region', 'created_at')),
            "tds": filtered_top_debtors,  # Use filtered TopDebtor data
            "upos": list(upos.values('id', 'description', 'depot', 'district', 'region', 'created_at')),
            "inspection_locations": inspection_locations, 
            "inspections_count": inspections_count,
            "mtn": mtn, 
            "maintenance_count": maintenance_values_list, 
            "maintenance_locations": maintenance_keys_list
        }

    return JsonResponse(data, safe=False)


@login_required(login_url='/accounts/login/')
def dashboard_index(request):
    
    user_title = request.user.get_full_name()
    url_path = request.path.split("/")
    
    user = request.user
    user_profile = UserProfile.objects.filter(id=user.id).first()
    
    section = user_profile.section
    depot = user_profile.depot
    district = user_profile.district
    region = user_profile.region
    sections = Sections.objects.all()
    depots = Depots.objects.all()
    districts = Districts.objects.all()
    regions = Regions.objects.all()

    # fetch pbnc data
    pbncs = PBNC.objects.all().order_by('-amount')
    tds = TD.objects.all().order_by('-amount')
    upos = UPO.objects.all()
    
    month_id = datetime.now().month
    current_month = {
        "id": month_id,
        "name": MONTHS[month_id-1]
    }

    return render(request, 
                  'dashboards/index.html', 
                  {
                      "user_title": user_title,
                      "page_title": "Dashboards",
                      "sections": sections,
                      "depots": depots,
                      "districts": districts,
                      "regions": regions,
                      "section": section,
                      "depot": depot,
                      "district": district,
                      "region": region,
                      "current_month": current_month,
                      "pbncs": pbncs, 
                      "tds": tds, 
                      "upos": upos
                  })
    
@login_required
def dsm_dashboard(request):
    
    user_title = request.user.get_full_name()
    
    return render(request, 'dashboards/commercial/index.html', {
                      "user_title": user_title,
                      "page_title": "DSM Dashboards"
                      })

@login_required
def upload_net_metering_register(request):
    
    if request.method == 'POST':
        print("request.POST: ", request.POST)
        csvfile = request.FILES['uploaded_file']
        print("csvfile: ", csvfile)
        
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)
        for row in reader:
            print("row: ", row)
            district_name = get_district_name(row['district'])
            print("district_name: ", district_name)
            district = Districts.objects.filter(district=district_name).first() if district_name else None
            print("district: ", district)
            try:
                date_applied = datetime.strptime(row['date_applied'], "%d-%b-%y")
            except ValueError:
                try:
                    date_applied = datetime.strptime(row['date_applied'], "%Y-%m-%d")
                except ValueError:
                    print(f"Could not parse date_applied: {row['date_applied']}")
                    continue

            try:
                date_commissioned = datetime.strptime(row['date_commissioned'], "%d-%b-%y") 
            except ValueError:
                try:
                    date_commissioned = datetime.strptime(row['date_commissioned'], "%Y-%m-%d")
                except ValueError:
                    print(f"Could not parse date_commissioned: {row['date_commissioned']}")
                    continue
            try:
                NetMeteringRegister.objects.create(
                    name_of_customer=row['name_of_customer'],
                    district=district,
                    date_applied=date_applied,
                    address=row['address'],
                    date_commissioned=date_commissioned,
                    progress=row['progress'],
                    installed_capacity=row['installed_capacity'],
                    duration=row['duration'],
                    inverter_type=row['inverter_type'],
                    solar_panel_type=row['solar_panel_type'],
                    customer_category=row['customer_category'],
                    phases=row['phases'],
                    email_address=row['email_address'],
                    cell_number=row['cell_number'],
                    meter_number=row['meter_number'],
                    account_number=row['account_number'],
                    ip_address=row['ip_address'],
                    comment=row['comment'],
                )
                print("success")
            except Exception as e:
                print("error: ", e)
    
    return render(request, 'dashboards/commercial/upload_net_metering_register.html', {})

@csrf_exempt
def get_net_metering_register(request):
    net_metering_register = NetMeteringRegister.objects.all()
    
    # Calculate total and commissioned applications quantum
    total_quantum = sum(float(record.installed_capacity or 0) for record in net_metering_register)
    commissioned_quantum = sum(
        float(record.installed_capacity or 0) 
        for record in net_metering_register 
        if record.progress == 'CD'  # CD = Commissioned
    )
    
    # Calculate total and commissioned applications count
    total_applications = net_metering_register.count()
    commissioned_applications = net_metering_register.filter(progress='CD').count()
    
    # Calculate exports and imports
    imports = net_metering_register.filter(customer_category='D')
    exports = net_metering_register.filter(customer_category='C')
    total_exports = sum(float(record.installed_capacity or 0) for record in exports)
    total_imports = sum(float(record.installed_capacity or 0) for record in imports)
    
    # Calculate percentages
    quantum_percentage = (commissioned_quantum / total_quantum * 100) if total_quantum else 0
    applications_percentage = (commissioned_applications / total_applications * 100) if total_applications else 0
    export_import_ratio = (total_exports / total_imports * 100) if total_imports else 0
    
    stats = {
        "net_metering_stats": [
            {
                "title": "Net Metering Applications Quantum (KW)",
                "percentage": f"{quantum_percentage:.1f}% Commissioned",
                "percentage_width": f"{quantum_percentage:.1f}%",
                "datasets": [
                    {
                        "label": "Total Applications Quantum (KW)",
                        "value": f"{total_quantum:.2f}"
                    },
                    {
                        "label": "Commissioned Quantum (KW)",
                        "value": f"{commissioned_quantum:.2f}"
                    }
                ]
            },
            {
                "title": "Net Metering Points Commissioned Applications",
                "percentage": f"{applications_percentage:.1f}% Commissioned",
                "percentage_width": f"{applications_percentage:.1f}%",
                "datasets": [
                    {
                        "label": "Total Applications",
                        "value": str(total_applications)
                    },
                    {
                        "label": "Commissioned Applications",
                        "value": str(commissioned_applications)
                    }
                ]
            },
            {
                "title": "Exports to Import ratio after Net Metering Commissioning",
                "percentage": f"{export_import_ratio:.1f}% Export to Import Ratio",
                "percentage_width": f"{export_import_ratio:.1f}%",
                "datasets": [
                    {
                        "label": "Total Exports (KWH)",
                        "value": f"{total_exports:.2f}"
                    },
                    {
                        "label": "Total Imports (KWH)",
                        "value": f"{total_imports:.2f}"
                    }
                ]
            }
        ]
    }
    
    return JsonResponse(stats)

@login_required
def upload_dsm_audit(request):
    if request.method == 'POST':
        print("request.POST: ", request.POST)
        csvfile = request.FILES['uploaded_file']
        print("csvfile: ", csvfile)
        
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)
        for row in reader:
            print("row: ", row)
            region = Regions.objects.filter(region=row['region']).first()
            if not region:
                messages.error(request, f"Region '{row['region']}' not found")
                continue
            try:
                DSMAudits.objects.create(
                    client=row['client'],  # Handle BOM in CSV
                    region=region
                )
            except Exception as e:
                messages.error(request, f"Error creating audit for {row['ï»¿client']}: {str(e)}")
                continue
        messages.success(request, "DSM Audit uploaded successfully")
        return redirect('/dashboards/dsm/upload_dsm_audits')
        
    return render(request, 'dashboards/commercial/upload_dsm_audits.html', {})

@csrf_exempt
def get_dsm_audits(request):
    dsm_audits = DSMAudits.objects.all()
    print("dsm_audits: ", dsm_audits)
    audits_by_region = {}
    for audit in dsm_audits:
        region_name = audit.region.region
        if region_name not in audits_by_region:
            audits_by_region[region_name] = 0
        audits_by_region[region_name] += 1

    # Ensure all regions are represented, even with 0 audits
    all_regions = ["Harare", "Southern", "Eastern", "Western", "Northern"] 
    for region in all_regions:
        if region not in audits_by_region:
            audits_by_region[region] = 0

    response = []
    for region, count in audits_by_region.items():
        response.append({
            "region": region,
            "audits": count
        })
    print("response: ", response)
    return JsonResponse(response, safe=False)

@login_required
def upload_net_metering_billing(request):
    if request.method == 'POST':
        print("request.POST: ", request.POST)
        csvfile = request.FILES['uploaded_file']
        print("csvfile: ", csvfile)
        
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)
        for row in reader:
            print("row: ", row)
            region = Regions.objects.filter(region=row['region']).first()
            # if not region:
            #     messages.error(request, f"Region '{row['region']}' not found")
            #     continue
            NetMeteringBilling.objects.create(
                commissioned_points=row['commissioned_points'],
                billed_points=row['billed_points'],
                region=region
            )
        messages.success(request, "Net Metering Billing uploaded successfully")
        return redirect('/dashboards/dsm/upload_net_metering_billing')

    return render(request, 'dashboards/commercial/upload_net_metering_billing.html', {})

@csrf_exempt
def get_net_metering_billing(request):
    net_metering_billing = NetMeteringBilling.objects.all()
    billing_by_region = {}
    for billing in net_metering_billing:
        region_name = billing.region.region
        if region_name not in billing_by_region:
            billing_by_region[region_name] = {
                'commissioned_points': 0,
                'billed_points': 0
            }
        billing_by_region[region_name]['commissioned_points'] += int(billing.commissioned_points)
        billing_by_region[region_name]['billed_points'] += int(billing.billed_points)

    response = []
    for region, stats in billing_by_region.items():
        percentage = 0
        if stats['commissioned_points'] > 0:
            percentage = round((stats['billed_points'] / stats['commissioned_points']) * 100, 2)
            
        response.append({
            'region': region,
            'commissionedPoints': stats['commissioned_points'],
            'totalBilled': stats['billed_points'], 
            'percentageBilled': percentage
        })

    # Add ZETDC total
    total_commissioned = sum(item['commissioned_points'] for item in billing_by_region.values())
    total_billed = sum(item['billed_points'] for item in billing_by_region.values())
    total_percentage = 0
    if total_commissioned > 0:
        total_percentage = round((total_billed / total_commissioned) * 100, 2)

    response.append({
        'region': 'ZETDC',
        'commissionedPoints': total_commissioned,
        'totalBilled': total_billed,
        'percentageBilled': total_percentage
    })
    return JsonResponse(response, safe=False)

@login_required
def upload_virtual_power_stats(request):
    if request.method == 'POST':
        print("request.POST: ", request.POST)
        csvfile = request.FILES['uploaded_file']
        print("csvfile: ", csvfile)
        
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)
        for row in reader:
            print("row: ", row)
            VirtualPowerStats.objects.create(
                dsm_initiative=row['dsm_initiative'],
                initiative_type=row['initiative_type'],
                initiative_value=row['initiative_value'],
                demand_curtailed=row['demand_curtailed']
            )
        messages.success(request, "Virtual Power Stats uploaded successfully")
        return redirect('/dashboards/dsm/upload_virtual_power_stats')

    return render(request, 'dashboards/commercial/upload_virtual_power_stats.html', {})

@csrf_exempt
def get_virtual_power_stats(request):
    virtual_power_stats = list(VirtualPowerStats.objects.values('dsm_initiative', 'initiative_type', 'initiative_value', 'demand_curtailed'))
    return JsonResponse(virtual_power_stats, safe=False)

def get_district_name(district):
    district_name = None
    if district == "HE":
        district_name = "HR EAST DISTRICT"
    elif district == "HS":
        district_name = "HR SOUTH DISTRICT"
    elif district == "HW":
        district_name = "HR WEST DISTRICT"
    elif district == "HN":
        district_name = "HR NORTH DISTRICT"
    elif district == "Byo East":
        district_name = "BYO EAST DISTRICT"
    elif district == "Byo West":
        district_name = "BYO WEST DISTRICT"
    elif district == "Byo Central":
        district_name = "BYO CENTRAL DISTRICT"
    elif district == "Byo North":
        district_name = "BYO NORTH DISTRICT"
    elif district == "Byo South":
        district_name = "BYO SOUTH DISTRICT"
    elif district == "Beitbridge":
        district_name = "BEITBRIDGE DISTRICT"
    elif district == "Victoria Falls":
        district_name = "VICTORIA FALLS DISTRICT"
    elif district == "MARONDERA":
        district_name = "MARONDERA DISTRICT"
    elif district == "BINDURA":
        district_name = "BINDURA DISTRICT"
    elif district == "KADOMA":
        district_name = "KADOMA DISTRICT"
    elif district == "BINDURA":
        district_name = "BINDURA DISTRICT"
    elif district == "CHINHOYI":
        district_name = "CHINHOYI DISTRICT"
    elif district == "GWERU":
        district_name = "GWERU DISTRICT"
    elif district == "MASVINGO":
        district_name = "MASVINGO DISTRICT"
    elif district == "MANICALAND":
        district_name = "MANICALAND DISTRICT"
    elif district == "MUTARE":
        district_name = "MUTARE DISTRICT"
    elif district == "Triangle":
        district_name = "TRIANGLE DISTRICT"
    return district_name

@login_required
def dashboard_filter(request, item):
    
    page_title = ""
    district_ = None
    region_ = None
    month_id = datetime.now().month
    current_month = {
        "id": month_id,
        "name": MONTHS[month_id-1]
    }
    user = request.user
    user_profile = UserProfile.objects.filter(id=user.id).first()
    _section = user_profile.section
    _district = user_profile.district
    _region = user_profile.region
    
    sections = Sections.objects.all()
    districts = Districts.objects.all()
    regions = Regions.objects.all()
    # fetch pbnc data
    if item == "district":
        district_id = request.POST['selectedDistrict']
        district_query = Districts.objects.filter(id=district_id).first()
        district_ = district_query
        district = district_query.district
        page_title = district
        pbncs = PBNC.objects.filter(region=region_query, district=district_query, depot=depot_query).all().order_by('-amount')
        tds = TD.objects.filter(district=district).all().order_by('-amount')
        upos = UPO.objects.filter(district=district).all()
        inpections = Inspections.objects.filter(district=district).all()
        maintenance_ = Maintenance.objects.filter(district=district).all()
        depots = Depots.objects.filter(district_id=district_id).all()
        
    elif item == "region":
        region_id = request.POST['selectedRegion']
        region_query = Regions.objects.filter(id=region_id).first()
        region_ = region_query
        region = region_query.region
        page_title = region
        pbncs = PBNC.objects.filter(region=region).all().order_by('-amount')
        tds = TD.objects.filter(region=region).all().order_by('-amount')
        upos = UPO.objects.filter(region=region).all()
        inpections = Inspections.objects.filter(region=region).all()
        maintenance_ = Maintenance.objects.filter(region=region).all()
        depots = Depots.objects.filter(region_id=region_id).all()
    elif item == "depot":
        depot_id = request.POST['selectedDepot']
        depot_query = Depots.objects.filter(id=depot_id).first()
        depot = depot_query.depot
        page_title = depot
        pbncs = PBNC.objects.filter(depot=depot).all().order_by('-amount')
        tds = TD.objects.filter(depot=depot).all().order_by('-amount')
        upos = UPO.objects.filter(depot=depot).all()
        inpections = Inspections.objects.filter(depot=depot).all()
        maintenance_ = Maintenance.objects.filter(depot=depot).all()
    
    # loop through inspections and foreach get record count from Files.
    inspection_count = {}
    for inspection in inpections:
        inspection_name = str(inspection.depot)
        inspection_month = inspection.created_at.month
        if inspection_month == month_id:
            if inspection_name in inspection_count:
                if inspection_count[inspection_name] > 0:
                    inspection_count[inspection_name] = inspection_count[inspection_name] + 1
            else:
                inspection_count[inspection_name] = 1 
    
    keys_list = json.dumps(list(inspection_count.keys()), default=str)
    values_list = json.dumps(list(inspection_count.values()), default=str)
    
    # loop through maintences and foreach get record count from Files.
    maintenance_count = {}
    for maintenance in maintenance_:
        maintenance_name = str(maintenance.depot)
        mmt_month = maintenance.created_at.month
        if mmt_month == month_id:
            if maintenance_name in maintenance_count:
                if maintenance_count[maintenance_name] > 0:
                    maintenance_count[maintenance_name] = maintenance_count[maintenance_name] + 1
            else:
                maintenance_count[maintenance_name] = 1 
    
    maintenance_keys_list = json.dumps(list(maintenance_count.keys()), default=str)
    maintenance_values_list = json.dumps(list(maintenance_count.values()), default=str)
    
    mtn = {}
    for depot in depots:
        maintenance_december = Maintenance.objects.filter(depot=depot.depot, created_at__month=month_id)
        maintenance_weekly_count = maintenance_december.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

        week_count = []
        for i in range(4):
            if i < len(maintenance_weekly_count):
                week_count.append(maintenance_weekly_count[i]['count'])
            else:
                week_count.append(0)
                
        mtn[depot.depot] = week_count
    
    user_title = request.user.get_full_name()
    url_path = request.path.split("/")
    print("url_path: ", url_path)
    
    return render(request, 
                  'dashboards/index.html', 
                  {
                      "user_title": user_title,
                      "page_description": page_title,
                      "section": _section if _section else None,
                      "district": district_ if district_ else _district,
                      "region": region_ if region_ else _region,
                      "sections": sections,
                      "districts": districts,
                      "regions": regions,
                      "url_path": url_path,
                      "current_month": current_month,
                      "pbncs": pbncs, 
                      "tds": tds, 
                      "upos": upos, 
                      "inspection_locations": keys_list, 
                      "inspections_count": values_list, 
                      "mtn": json.dumps(mtn, default=str), 
                      "maintenance_count": maintenance_values_list, 
                      "maintenance_locations": maintenance_keys_list, 
                      "maintenance_": serializers.serialize('json', maintenance_), 
                      "inspections_": serializers.serialize('json', inpections) 
                  })

def on_filter(request, item):

    month_id = datetime.now().month
    current_month = {
        "id": month_id,
        "name": MONTHS[month_id-1]
    }


    region_id = request.POST['selectedRegion']
    district_id = request.POST['selectedDistrict']
    depot_id = request.POST['selectedDepot']
    
    region_query = Regions.objects.filter(id=region_id).first()
    district_query = Districts.objects.filter(id=district_id).first()
    depot_query = Depots.objects.filter(id=depot_id).first()
    
    pbncs = PBNC.objects.filter(region=region_query, district=district_query, depot=depot_query).all().order_by('-amount')
    tds = TD.objects.filter(region=region_query, district=district_query, depot=depot_query).all().order_by('-amount')
    upos = UPO.objects.filter(region=region_query, district=district_query, depot=depot_query).all()
    inpections = Inspections.objects.filter(region=region_query, district=district_query, depot=depot_query).all()
    maintenance_ = Maintenance.objects.filter(region=region_query, district=district_query, depot=depot_query).all()
    # here
    depots = Depots.objects.filter(region_id=region_query, district_id=district_query).all()

    keys_list, values_list = get_inspections_monthly(inpections, month_id)
    
    # loop through maintences and foreach get record count from Files.
    maintenance_keys_list, maintenance_values_list = get_mmt_monthly(maintenance_, month_id)
    
    mtn = get_mmt_weekly(depots, month_id)
    
    inspection_locations = keys_list
    inspections_count = values_list

    data = {
            "pbncs": list(pbncs.values('id', 'name', 'amount', 'depot', 'district', 'region', 'created_at')),
            "tds": list(tds.values('id', 'name', 'amount', 'depot', 'district', 'region', 'created_at')),
            "upos": list(upos.values('id', 'description', 'depot', 'district', 'region', 'created_at')),
            "inspection_locations": inspection_locations, 
            "inspections_count": inspections_count,
            "mtn": mtn, 
            "maintenance_count": maintenance_values_list, 
            "maintenance_locations": maintenance_keys_list
        }

    return JsonResponse(data, safe=False)

@csrf_exempt
def dashboards_maintenance_ajax(request):
    month = request.GET['month']
    user_ = request.user
    user_profile = UserProfile.objects.filter(id=user_.id).first()
    mtn = {}
    current_month = {
        "id": month,
        "name": MONTHS[int(month)-1]
    }
    mtn = get_mmt(user_profile, month)
    
    return JsonResponse(mtn, safe=False)

@csrf_exempt
def dashboards_inspections_ajax(request):
    month = request.GET['month']
    user_ = request.user
    user_profile = UserProfile.objects.filter(id=user_.id).first()
    keys_list, values_list = get_inspections_bargraph(user_profile, month)
    
    return JsonResponse({
        "keys_list": keys_list,
        "values_list": values_list
        }, safe=False)

@login_required
def pbnc_upload(request):
    if request.method == 'POST':

        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:        
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")

            district = Districts.objects.filter(district=row['district']).first()
            depot = Depots.objects.filter(depot=row['depot']).first()
            region = Regions.objects.filter(region=row['region']).first()
            
            new_pbnc = PBNC(
                name=row['name'],
                amount=row['amount'],
                depot=depot,
                district=district,
                region=region,
                created_at=formatted_date
            )
            new_pbnc.save()
        
        redirect('/dashboards/pbnc/upload')
            
    return render(request, 'dashboards/pbnc/upload.html', {})

@login_required
def td_upload(request):
    if request.method == 'POST':
        
        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
            
            district = Districts.objects.filter(district=row['district']).first()
            depot = Depots.objects.filter(depot=row['depot']).first()
            region = Regions.objects.filter(region=row['region']).first()
            
            new_td = TD(
                name=row['name'],
                amount=row['amount'],
                depot=depot,
                district=district,
                region=region,
                created_at=formatted_date
            )
            new_td.save()
        
        redirect('/dashboards/td/upload')
            
    return render(request, 'dashboards/td/upload.html', {})
@login_required
def upo_upload(request):
    if request.method == 'POST':
        
        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
                        
            district = Districts.objects.filter(district=row['district']).first()
            depot = Depots.objects.filter(depot=row['depot']).first()
            region = Regions.objects.filter(region=row['region']).first()
            
            new_upo = UPO(
            description=row['description'],
            depot=depot,
            district=district,
            region=region,
            created_at=formatted_date
             
            )
            new_upo.save()
        
        redirect('/dashboards/upo/upload')
            
    return render(request, 'dashboards/upo/upload.html', {})
@login_required
def inspections_upload(request):
    if request.method == 'POST':
        
        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
            district = Districts.objects.filter(district=row['district']).first()
            depot = Depots.objects.filter(depot=row['depot']).first()
            region = Regions.objects.filter(region=row['region']).first()
            
            new_inps = Inspections(
                location=row['location'],
                depot=depot,
                district=district,
                region=region,
                created_at=formatted_date
            )
            new_inps.save()
        
        redirect('/dashboards/inspections/upload')
            
    return render(request, 'dashboards/inspections/upload.html', {})
@login_required
def maintenance_upload(request):
    if request.method == 'POST':
        
        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
            district = Districts.objects.filter(district=row['district']).first()
            depot = Depots.objects.filter(depot=row['depot']).first()
            region = Regions.objects.filter(region=row['region']).first()
            new_maintenance = Maintenance(
                location=row['location'],
                depot=depot,
                district=district,
                region=region,
                created_at=formatted_date
            )
            new_maintenance.save()
        
        redirect('/dashboards/maintenance/upload')
            
    return render(request, 'dashboards/maintenance/upload.html', {})
