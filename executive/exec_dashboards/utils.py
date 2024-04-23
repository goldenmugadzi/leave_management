import json
from executive.exec_dashboards.models import *
from it.users.models import *
from django.db.models.functions import ExtractWeek
from django.db.models import Count

def get_inspections(user, month_id):
    inspections = []
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.section if user.section else None
        if depot:
            if depot.id:
                inspections = Inspections.objects.filter(depot=depot.id, created_at__month=month_id)
    if any(role.role == 'district_manager' for role in user.roles.all()):
        district = user.district if user.district else None
        if district and district:
            inspections = Inspections.objects.filter(district=district.id, created_at__month=month_id)
    if any(role.role == 'executive' for role in user.roles.all()):
        region = user.region if user.region else None
        if region:
            if region.id:
                inspections = Inspections.objects.filter(region=region.id, created_at__month=month_id)
    return inspections

def get_inspections_bargraph(user, month_id):
    keys_list, values_list = [], []
    region_ = Regions.objects.filter(id=user.region.id).first() if user.region else None if user.region else None
    district = user.district if user.district else None
    depot = user.section if user.section else None
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.depot if user.depot else None
        depots = Depots.objects.filter(id=depot.id).all()
        if depot:
            inspections = [
            inspection for depot in depots
            for inspection in Inspections.objects.filter(depot=depot.id, created_at__month=month_id).all()
            ]
            keys_list, values_list = get_inspections_monthly(inspections, month_id)
    if any(role.role == 'district_manager' for role in user.roles.all()):
        if district:
            depots = Depots.objects.filter(district_id=district.id).all()
            inspections = [
            inspection for depot in depots
            for inspection in Inspections.objects.filter(depot=depot.id, created_at__month=month_id).all()
            ]
            keys_list, values_list = get_inspections_monthly(inspections, month_id)
    if any(role.role == 'executive' for role in user.roles.all()):
        if region_:
            depots = Depots.objects.filter(region_id=region_.id).all()
            if region_:
                inspections = [
                inspection for depot in depots
                for inspection in Inspections.objects.filter(depot_id=depot.id, created_at__month=month_id).all()
                ]
                keys_list, values_list = get_inspections_monthly(inspections, month_id)
    return keys_list, values_list

def get_inspections_bargraph_filter(selected_region, selected_district, selected_depot, month_id, user):
    keys_list, values_list = [], []
    region_, district, depot = None, None, None
    print("parameters: ", selected_region, selected_district, selected_depot)
    if selected_region:
        print("selected_region", selected_region)
        region_ = Regions.objects.filter(id=selected_region).first()
        depots = Depots.objects.filter(region_id=region_.id).all()
        if region_:
            inspections = [
            inspection for depot in depots
            for inspection in Inspections.objects.filter(depot_id=depot.id, created_at__month=month_id).all()
            ]
            keys_list_2, values_list_2 = get_inspections_monthly_filter(inspections, month_id)
            keys_list.extend(keys_list_2)
            values_list.extend(values_list_2)

    if selected_district:
        print("selected_district", selected_district)
        district = Districts.objects.filter(id=selected_district).first()
        depots = Depots.objects.filter(district_id=district.id).all()
        if district:
            inspections = [
            inspection for depot in depots
            for inspection in Inspections.objects.filter(depot=depot.id, created_at__month=month_id).all()
            ]
            keys_list_1, values_list_1 = get_inspections_monthly_filter(inspections, month_id)
            keys_list.extend(keys_list_1)
            values_list.extend(values_list_1)
    
    if selected_depot:
        print("selected_depot", selected_depot)
        depot = Depots.objects.filter(id=selected_depot).first()
        depots = Depots.objects.filter(id=selected_depot).all()
        if depot:
            inspections = [
            inspection for depot in depots
            for inspection in Inspections.objects.filter(depot=depot.id, created_at__month=month_id).all()
            ]
            keys_list_, values_list_ = get_inspections_monthly_filter(inspections, month_id)
            keys_list.extend(keys_list_)
            values_list.extend(values_list_)

    keys_list = json.dumps(keys_list, default=str) if keys_list else []
    values_list = json.dumps(values_list, default=str) if values_list else []
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


def get_inspections_monthly_filter(inspections, month_id):
   
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
    keys_list = list(inspection_count.keys())
    values_list = list(inspection_count.values())
    return keys_list, values_list

def get_mmts(user, month_id):
    maintenances = []
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.section if user.section else None
        if depot:
            if depot.id:
                maintenances = Maintenance.objects.filter(depot=depot.id, created_at__month=month_id)
    if any(role.role == 'district_manager' for role in user.roles.all()):
        district = user.district if user.district else None
        if district and district:
            maintenances = Maintenance.objects.filter(district=district.id, created_at__month=month_id)
    if any(role.role == 'executive' for role in user.roles.all()):
        region = user.region if user.region else None
        if region:
            if region.id:
                maintenances = Maintenance.objects.filter(region=region.id, created_at__month=month_id)
    return maintenances

def get_mmt(user, month_id):
    mtn = {}
    if any(role.role == 'fore_person' for role in user.roles.all()):
        depot = user.section if user.section else None
        if depot:
            if depot.id:
                maintenance_december = Maintenance.objects.filter(depot=depot.id, created_at__month=month_id)
            maintenance_weekly_count = maintenance_december.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

            week_count = []
            for i in range(4):
                if i < len(maintenance_weekly_count):
                    week_count.append(maintenance_weekly_count[i]['count'])
                else:
                    week_count.append(0)
                    
            mtn[depot.section] = week_count
            
    if any(role.role == 'district_manager' for role in user.roles.all()):
        depots = Depots.objects.filter(district_id=user.district.id).all()
        district = user.district if user.district else None
        if district and district:
            for depot in depots:
                maintenance_december = Maintenance.objects.filter(depot=depot.id, district=district.id, created_at__month=month_id)
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
        region = user.region if user.region else None
        if region and region:
            for depot in depots:
                    maintenance_december = Maintenance.objects.filter(depot=depot.id, region=region.id, created_at__month=month_id)
                    maintenance_weekly_count = maintenance_december.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')
                    week_count = []
                    for i in range(4):
                        if i < len(maintenance_weekly_count):
                            week_count.append(maintenance_weekly_count[i]['count'])
                        else:
                            week_count.append(0)
                            
                    mtn[depot.depot] = week_count
    
    return mtn


def get_mmt_filter(selected_region, selected_district, selected_depot, month_id, user):
    mtn, maintenance_december = {}, None
    print("parameters: ", selected_region, selected_district, selected_depot)
    
    if selected_region:
        print("selected_region", selected_region)
        region_ = Regions.objects.filter(id=selected_region).first()
        depots = Depots.objects.filter(region_id=region_.id).all()
        if region_:
            for depot in depots:
                depot_inspections = Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id)
                if depot_inspections:
                    maintenance_weekly_count = depot_inspections.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

                    week_count = []
                    for i in range(4):
                        if i < len(maintenance_weekly_count):
                            week_count.append(maintenance_weekly_count[i]['count'])
                        else:
                            week_count.append(0)
                            
                    mtn[depot.depot] = week_count
    if selected_district:
        print("selected_district", selected_district)
        district = Districts.objects.filter(id=selected_district).first()
        depots = Depots.objects.filter(district_id=district.id).all()
        if district:
            for depot in depots:
                depot_inspections = Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id)
                if depot_inspections:
                    maintenance_weekly_count = depot_inspections.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

                    week_count = []
                    for i in range(4):
                        if i < len(maintenance_weekly_count):
                            week_count.append(maintenance_weekly_count[i]['count'])
                        else:
                            week_count.append(0)
                            
                    mtn[depot.depot] = week_count
    
    if selected_depot:
        print("selected_depot", selected_depot)
        depot = Depots.objects.filter(id=selected_depot).first()
        depots = Depots.objects.filter(id=selected_depot).all()
        if depot:
            for depot in depots:
                depot_inspections = Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id)
                if depot_inspections:
                    maintenance_weekly_count = depot_inspections.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

                    week_count = []
                    for i in range(4):
                        if i < len(maintenance_weekly_count):
                            week_count.append(maintenance_weekly_count[i]['count'])
                        else:
                            week_count.append(0)
                            
                    mtn[depot.depot] = week_count

    return mtn


def get_maintenance_linegraph(user, month_id):
    maintenance_keys_list, maintenance_values_list = [], []
    region_ = Regions.objects.filter(id=user.region.id).first() if user.region else None if user.region else None
    district = user.district if user.district else None
    depot = user.section if user.section else None
    
    if any(role.role == 'fore_person' for role in user.roles.all()):
        if depot:
            depots = Depots.objects.filter(id=depot.id).all()
            if depot:
                maintenances = [
                maintenance for depot in depots
                for maintenance in Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id).all()
                ]
                maintenance_keys_list, maintenance_values_list = get_mmt_monthly(maintenances, month_id)
    if any(role.role == 'district_manager' for role in user.roles.all()):
        print(district.district, region_, month_id)
        if district and district:
            depots = Depots.objects.filter(district_id=district.id).all()
            if district:
                maintenances = [
                maintenance for depot in depots
                for maintenance in Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id).all()
                ]
                maintenance_keys_list, maintenance_values_list = get_mmt_monthly(maintenances, month_id)
    if any(role.role == 'executive' for role in user.roles.all()):
        if region_:
            depots = Depots.objects.filter(region_id=region_.id).all()
            if region_:
                maintenances = [
                maintenance for depot in depots
                for maintenance in Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id).all()
                ]
                maintenance_keys_list, maintenance_values_list = get_mmt_monthly(maintenances, month_id)
                
    maintenance_keys_list = json.dumps(list(maintenance_keys_list), default=str)
    maintenance_values_list = json.dumps(list(maintenance_values_list), default=str)
    return maintenance_keys_list, maintenance_values_list


def get_maintenance_linegraph_filter(selected_region, selected_district, selected_depot, month_id, user):
    maintenance_keys_list, maintenance_values_list = [], []
    if selected_region:
        region_ = Regions.objects.filter(id=selected_region).first()
        depots = Depots.objects.filter(region_id=region_.id).all()
        if region_:
            maintenances = [
            maintenance for depot in depots
            for maintenance in Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id).all()
            ]
            maintenance_keys_list, maintenance_values_list = get_mmt_monthly(maintenances, month_id)

    if selected_district:
        district = Districts.objects.filter(id=selected_district).first()
        depots = Depots.objects.filter(district_id=district.id).all()
        if district:
            maintenances = [
            maintenance for depot in depots
            for maintenance in Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id).all()
            ]
            maintenance_keys_list, maintenance_values_list = get_mmt_monthly(maintenances, month_id)
    
    if selected_depot:
        depot = Depots.objects.filter(id=selected_depot).first()
        depots = Depots.objects.filter(id=depot.id).all()
        if depot:
            maintenances = [
            maintenance for depot in depots
            for maintenance in Maintenance.objects.filter(depot_id=depot.id, created_at__month=month_id).all()
            ]
            maintenance_keys_list, maintenance_values_list = get_mmt_monthly(maintenances, month_id)
    
    maintenance_keys_list = json.dumps(list(maintenance_keys_list), default=str)
    maintenance_values_list = json.dumps(list(maintenance_values_list), default=str)
    return maintenance_keys_list, maintenance_values_list


def get_mmt_weekly(depots, month_id):
    mtn = {}
    for depot in depots:
        maintenance_december = Maintenance.objects.filter(depot=depot.id, created_at__month=month_id)
        maintenance_weekly_count = maintenance_december.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

        week_count = []
        for i in range(4):
            if i < len(maintenance_weekly_count):
                week_count.append(maintenance_weekly_count[i]['count'])
            else:
                week_count.append(0)
                
        mtn[depot.depot] = week_count
    
    return mtn

def get_mmt_monthly(maintenances, month_id):
    maintenance_count = {}
    for maintenance in maintenances:
        maintenance_name = str(maintenance.depot)
        if maintenance_name in maintenance_count:
            if maintenance_count[maintenance_name] > 0:
                maintenance_count[maintenance_name] = maintenance_count[maintenance_name] + 1
        else:
           maintenance_count[maintenance_name] = 1 
    
    maintenance_keys_list = maintenance_count.keys()
    maintenance_values_list = maintenance_count.values()
    return maintenance_keys_list, maintenance_values_list
