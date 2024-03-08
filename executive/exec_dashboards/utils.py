import json
from executive.exec_dashboards.models import *
from it.users.models import *
from django.db.models.functions import ExtractWeek
from django.db.models import Count

def get_inspections(user, month_id):
    inspections = []
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.section if user.section else None
        if depot.id:
            inspections = Inspections.objects.filter(depot=depot.section, created_at__month=month_id)
    if any(role.role == 'district_manager' for role in user.roles.all()):
        district = user.district if user.district else None
        if district:
            inspections = Inspections.objects.filter(district=district.district, created_at__month=month_id)
    if any(role.role == 'executive' for role in user.roles.all()):
        region = user.region if user.region else None
        if region.id:
            inspections = Inspections.objects.filter(region=region.region, created_at__month=month_id)
    return inspections

def get_inspections_bargraph(user, month_id):
    keys_list, values_list = [], []
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.section if user.section else None
        if depot.id:
            inspections = Inspections.objects.filter(depot=depot.section, created_at__month=month_id)
            keys_list, values_list = get_inspections_monthly(inspections, month_id)
    if any(role.role == 'district_manager' for role in user.roles.all()):
        district = user.district if user.district else None
        if district:
            inspections = Inspections.objects.filter(district=district.district, created_at__month=month_id)
            keys_list, values_list = get_inspections_monthly(inspections, month_id)
    if any(role.role == 'executive' for role in user.roles.all()):
        region = user.region if user.region else None
        if region.id:
            inspections = Inspections.objects.filter(region=region.region, created_at__month=month_id)
            keys_list, values_list = get_inspections_monthly(inspections, month_id)
    return keys_list, values_list

def get_inspections_monthly(inspections, month_id):
   
    inspection_count = {}
    for inspection in inspections:
        inspection_name = str(inspection.depot)
        inspection_month = inspection.created_at.month
        if int(inspection_month) == int(month_id):
            if inspection_name in inspection_count:
                if inspection_count[inspection_name] > 0:
                    inspection_count[inspection_name] = inspection_count[inspection_name] + 1
            else:
                inspection_count[inspection_name] = 1 
    keys_list = json.dumps(list(inspection_count.keys()), default=str)
    values_list = json.dumps(list(inspection_count.values()), default=str)
    return keys_list, values_list

def get_mmts(user, month_id):
    maintenances = []
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.section if user.section else None
        if depot.id:
            maintenances = Maintenance.objects.filter(depot=depot.section, created_at__month=month_id)
    if any(role.role == 'district_manager' for role in user.roles.all()):
        district = user.district if user.district else None
        if district:
            maintenances = Maintenance.objects.filter(district=district.district, created_at__month=month_id)
    if any(role.role == 'executive' for role in user.roles.all()):
        region = user.region if user.region else None
        if region.id:
            maintenances = Maintenance.objects.filter(region=region.region, created_at__month=month_id)
    return maintenances

def get_mmt(user, month_id):
    mtn = {}
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.section if user.section else None
        if depot.id:
            maintenance_december = Maintenance.objects.filter(depot=depot.section, created_at__month=month_id)
            maintenance_weekly_count = maintenance_december.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

            week_count = []
            for i in range(4):
                if i < len(maintenance_weekly_count):
                    week_count.append(maintenance_weekly_count[i]['count'])
                else:
                    week_count.append(0)
                    
            mtn[depot.section] = week_count
            
    if any(role.role == 'district_manager' for role in user.roles.all()):
        depots = Depots.objects.filter(region_id=user.region.id).all()
        for depot in depots:
            district = user.district if user.district else None
            if district:
                maintenance_december = Maintenance.objects.filter(district=district.district, created_at__month=month_id)
                maintenance_weekly_count = maintenance_december.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

                week_count = []
                for i in range(4):
                    if i < len(maintenance_weekly_count):
                        week_count.append(maintenance_weekly_count[i]['count'])
                    else:
                        week_count.append(0)
                        
                mtn[depot.depot] = week_count
            
    if any(role.role == 'executive' for role in user.roles.all()):
        depots = Depots.objects.filter(region_id=user.region.id).all()
        for depot in depots:
            region = user.region if user.region else None
            if region:
                maintenance_december = Maintenance.objects.filter(region=region.region, created_at__month=month_id)
                maintenance_weekly_count = maintenance_december.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')
                week_count = []
                for i in range(4):
                    if i < len(maintenance_weekly_count):
                        week_count.append(maintenance_weekly_count[i]['count'])
                    else:
                        week_count.append(0)
                        
                mtn[depot.depot] = week_count
    
    return mtn

def get_mmt_weekly(depots, month_id):
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

def get_mmt_monthly(maintenances, month_id):
    maintenance_count = {}
    for maintenance in maintenances:
        maintenance_name = str(maintenance.depot)
        if maintenance_name in maintenance_count:
            if maintenance_count[maintenance_name] > 0:
                maintenance_count[maintenance_name] = maintenance_count[maintenance_name] + 1
        else:
           maintenance_count[maintenance_name] = 1 
    
    maintenance_keys_list = json.dumps(list(maintenance_count.keys()), default=str)
    maintenance_values_list = json.dumps(list(maintenance_count.values()), default=str)
    return maintenance_keys_list, maintenance_values_list

def get_maintenance_linegraph(user, month_id):
    maintenance_keys_list, maintenance_values_list = [], []
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.section if user.section else None
        if depot.id:
            maintenances = Maintenance.objects.filter(depot=depot.section, created_at__month=month_id)
            maintenance_keys_list, maintenance_values_list = get_inspections_monthly(maintenances, month_id)
    if any(role.role == 'district_manager' for role in user.roles.all()):
        district = user.district if user.district else None
        if district:
            maintenances = Maintenance.objects.filter(district=district.district, created_at__month=month_id)
            maintenance_keys_list, maintenance_values_list = get_inspections_monthly(maintenances, month_id)
    if any(role.role == 'executive' for role in user.roles.all()):
        region = user.region if user.region else None
        if region.id:
            maintenances = Maintenance.objects.filter(region=region.region, created_at__month=month_id)
            maintenance_keys_list, maintenance_values_list = get_inspections_monthly(maintenances, month_id)
    return maintenance_keys_list, maintenance_values_list
