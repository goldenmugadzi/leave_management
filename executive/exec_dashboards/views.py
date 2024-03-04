import csv
from datetime import datetime
import json
from django.http import JsonResponse
from django.shortcuts import render,redirect
from .models import PBNC, TD, UPO, Inspections, Maintenance
from django.core import serializers
from django.db.models import Count
from django.db.models.functions import ExtractWeek

from it.users.models import Sections, UserProfile, Depots, Districts, Regions

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# Create your views here.
def dashboard_index(request):
    
    user_title = request.user.get_full_name()
    user = request.user
    user_profile = UserProfile.objects.filter(id=user.id).first()
    l = request.user.groups.values_list('name',flat = True) # QuerySet Object
    user_groups = list(l) 
    
    # fetch pbnc data
    month_id = datetime.now().month
    current_month = {
        "id": month_id,
        "name": MONTHS[month_id-1]
    }
    pbncs = PBNC.objects.all().order_by('-amount')
    tds = TD.objects.all().order_by('-amount')
    upos = UPO.objects.all()
    inpections = Inspections.objects.all()
    maintenance_ = Maintenance.objects.all()
    depots = Depots.objects.all()
    districts = Sections.objects.all()
    regions = Regions.objects.all()

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
        
    print("mtn: ", mtn)
   
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
        if maintenance_name in maintenance_count:
            if maintenance_count[maintenance_name] > 0:
                maintenance_count[maintenance_name] = maintenance_count[maintenance_name] + 1
        else:
           maintenance_count[maintenance_name] = 1 
    
    maintenance_keys_list = json.dumps(list(maintenance_count.keys()), default=str)
    maintenance_values_list = json.dumps(list(maintenance_count.values()), default=str)
    
    user_title = request.user.get_full_name()
    url_path = request.path.split("/")
    
    return render(request, 
                  'dashboards/index.html', 
                  {
                      "user_title": user_title,
                      "url_path": url_path,
                      "page_title": "Dashboards",
                      "districts": districts,
                      "regions": regions,
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

def dashboard_filter(request, item):
    
    page_title = ""
    district_ = None
    region_ = None
    month_id = datetime.now().month
    current_month = {
        "id": month_id,
        "name": MONTHS[month_id-1]
    }
    # fetch pbnc data
    if item == "district":
        district_id = request.POST['selectedDistrict']
        district_query = Districts.objects.filter(id=district_id).first()
        district_ = district_query
        district = district_query.district
        page_title = district
        pbncs = PBNC.objects.filter(district=district).all().order_by('-amount')
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
                      "district": district_,
                      "region": region_,
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

def dashboards_maintenance_ajax(request):
    month = request.GET['month']
    
    mtn = {}
    current_month = {
        "id": month,
        "name": MONTHS[int(month)-1]
    }
    depots = Depots.objects.all()
    for depot in depots:
        maintenance_december = Maintenance.objects.filter(depot=depot.depot, created_at__month=month)
        maintenance_weekly_count = maintenance_december.annotate(week=ExtractWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

        week_count = []
        for i in range(4):
            if i < len(maintenance_weekly_count):
                week_count.append(maintenance_weekly_count[i]['count'])
            else:
                week_count.append(0)
                
        mtn[depot.depot] = week_count
    
    return JsonResponse(mtn, safe=False)

def pbnc_upload(request):
    if request.method == 'POST':

        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:        
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
            new_pbnc = PBNC(
                name=row['name'],
                amount=row['amount'],
                depot=row['depot'],
                district=row['district'],
                region=row['region'],
                created_at=formatted_date
            )
            new_pbnc.save()
        
        redirect('/dashboards/pbnc/upload')
            
    return render(request, 'dashboards/pbnc/upload.html', {})

def td_upload(request):
    if request.method == 'POST':
        
        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
            new_td = TD(
                name=row['name'],
                amount=row['amount'],
                depot=row['depot'],
                district=row['district'],
                region=row['region'],
                created_at=formatted_date
            )
            new_td.save()
        
        redirect('/dashboards/td/upload')
            
    return render(request, 'dashboards/td/upload.html', {})

def upo_upload(request):
    if request.method == 'POST':
        
        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
            new_upo = UPO(
            description=row['description'],
            depot=row['depot'],
            district=row['district'],
            region=row['region'],
            created_at=formatted_date
             
            )
            new_upo.save()
        
        redirect('/dashboards/upo/upload')
            
    return render(request, 'dashboards/upo/upload.html', {})

def inspections_upload(request):
    if request.method == 'POST':
        
        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
            
            new_inps = Inspections(
                location=row['location'],
                depot=row['depot'],
                district=row['district'],
                region=row['region'],
                created_at=formatted_date
            )
            new_inps.save()
        
        redirect('/dashboards/inspections/upload')
            
    return render(request, 'dashboards/inspections/upload.html', {})

def maintenance_upload(request):
    if request.method == 'POST':
        
        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")
            new_maintenance = Maintenance(
                location=row['location'],
                depot=row['depot'],
                district=row['district'],
                region=row['region'],
                created_at=formatted_date
            )
            new_maintenance.save()
        
        redirect('/dashboards/maintenance/upload')
            
    return render(request, 'dashboards/maintenance/upload.html', {})