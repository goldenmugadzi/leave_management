from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect
#from .model import TransportAssets
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from.models import TransportAssets
import json
import csv
from django.http import HttpResponse
from datetime import date, datetime 
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
#from exchangelib import Credentials, Account, Configuration, Message, Mailbox
from django.urls import reverse
from django.template.loader import render_to_string
#from exchangelib import HTMLBody
from.models import*
from it.users.models import Regions, Sections, UserProfile,Designations,CostCenter
from.forms import TransportAssetsForm

@login_required
def register_vehicle(request):
   if request.method == 'POST':
        form = TransportAssetsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  
            return redirect('table_vehicle') 
        else:
        
            print(form.errors)  
   else:
        form = TransportAssetsForm()

   return render(request, "transport/register_vehicle.html", {"form": form})

@login_required
def table_vehicle (request):
  return render(request,'transport/table_vehicle.html')

@login_required
def vehicle_datatable(request):

    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        transportAssets = TransportAssets.objects.all()

        if search_value:
            transportAssets = transportAssets.filter(
                Q(jobcardnumber__icontains=search_value) |
                Q(fleet_number__icontains=search_value) |
                Q(reg_number__icontains=search_value) |
                Q(user__username__icontains=search_value) |
                Q(sections__section_name__icontains=search_value) | 
                Q(fuel_type__icontains=search_value) |
                Q(designations__designation__icontains=search_value) |
                Q(regions__region__icontains=search_value)
            )

        total = transportAssets.count()

        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column is not None and order_dir is not None:
            column_map = {
                "0": "jobcardnumber",
                "1": "fleet_number",
                "2": "reg_number",
                "3": "department",
                "4": "regions",
                "5": "user",
                "6": "designations",
                "7": "model",
                "8": "fuel_type",
                "9": "year",
                "11": "chass_number",
                "12": "status",
            }

            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}'
                transportAssets = transportAssets.order_by(column_name)

        paginator = Paginator(transportAssets, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)

        data = []
        for transportAsset in page_obj:
            o = {
                "id": transportAsset.id,
                "jobcardnumber": transportAsset.jobcardnumber,
                "fleet_number": transportAsset.fleet_number,
                "reg_number": transportAsset.reg_number,
                "user": f"{transportAsset.user.first_name} {transportAsset.user.last_name}" if transportAsset.user else None,
                "make": transportAsset.make,
                "model": transportAsset.model,
                "engine_number": transportAsset.engine_number,
                "chass_number": transportAsset.chass_number,
                "year": transportAsset.year,
                "updated_by": transportAsset.updated_by,
                "created_by": f"{transportAsset.created_by.first_name} {transportAsset.created_by.last_name}" if transportAsset.created_by else None,
                "department": transportAsset.department.section if transportAsset.department else None,
                "regions": transportAsset.regions.region if transportAsset.regions else None,
                "fuel_type": transportAsset.fuel_type,
                "designation": transportAsset.designation.description if transportAsset.designation else None,
                "status": transportAsset.status,
                "cost_center": transportAsset.cost_center.name if transportAsset.cost_center else None,
            }
            data.append(o)

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        })
    except Exception as ex:
        print(ex)
        return JsonResponse({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

@login_required
def update_vehicle(request, id):
    transportAssets = TransportAssets.objects.filter(id=id).first()
    
    if request.method == 'POST':
        region_id = request.POST['regions']
        regions = Regions.objects.filter(id=region_id).first()

        transportAssets.fleet_number = request.POST['fleet_number']
        transportAssets.reg_number = request.POST['reg_number']
        transportAssets.make = request.POST['make']
        transportAssets.regions = regions
        transportAssets.model = request.POST['model']
        transportAssets.engine_number = request.POST['engine_number']
        transportAssets.chass_number = request.POST['chass_number']
        transportAssets.fuel_type = request.POST['fuel_type']
        transportAssets.year = request.POST['year']
        transportAssets.status = request.POST['status']
        
        # Set updated_by to the name of the currently logged-in user
        if request.user.is_authenticated:
            transportAssets.updated_by = f"{request.user.first_name} {request.user.last_name}"
        else:
            transportAssets.updated_by = "Anonymous User"
        
        transportAssets.save()

        return redirect('/table_vehicle')
    
    return render(request, 'transport/update_vehicle.html', {
        'transportAssets': transportAssets,
        'id': transportAssets.id,
        'fleet_number': transportAssets.fleet_number,
        'reg_number': transportAssets.reg_number,
        'make': transportAssets.make,
        'asset_number': transportAssets.id,  
        'regions': transportAssets.regions,
        'model': transportAssets.model,
        'engine_number': transportAssets.engine_number,
        'chass_number': transportAssets.chass_number,
        'year': transportAssets.year,
        'fuel_type': transportAssets.fuel_type,
        'updated_by': transportAssets.updated_by, 
        'sections': Sections.objects.all(),
        'users': UserProfile.objects.all(),
        'regions': Regions.objects.all(),
        'designations': Designations.objects.all(),
    })

@login_required
def upload_vehicle(request):
    if request.method == 'POST':
        csvfile = request.FILES.get('uploaded_csv')
        
        if not csvfile:
            return render(request, 'transport/upload_vehicle.html', {'error': 'No file uploaded'})

        try:
            decoded_file = csvfile.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            success_count = 0
            error_messages = []

            for row in reader:
                try:
                    # Get or create section
                    section_name = row.get('section', '').strip()
                    if not section_name:
                        raise ValueError("Section is required")
                    section, _ = Sections.objects.get_or_create(section=section_name)

                    # Get user
                    user_name = row.get('user', '').strip()
                    if not user_name:
                        raise ValueError("User is required")
                    user_profile = UserProfile.objects.get(username=user_name)

                    # Get or set default region
                    region_name = row.get('region', '').strip()
                    region = Regions.objects.filter(region=region_name).first() if region_name else None

                    # Create TransportAssets with all required fields
                    TransportAssets.objects.create(
                        fleet_number=row.get('fleet_number', '').strip(),
                        reg_number=row.get('reg_number', '').strip(),
                        make=row.get('make', '').strip(),
                        user=user_profile,
                        department=section,
                        regions=region,
                        model=row.get('model', '').strip(),
                        engine_number=row.get('engine_number', '').strip(),
                        chass_number=row.get('chass_number', '').strip(),
                        fuel_type=row.get('fuel_type', 'Petrol').strip(),  # Default to Petrol
                        year=row.get('year', '').strip(),
                        status=row.get('status', 'Active').strip(),  # Default to Active
                        updated_by=f"{request.user.first_name} {request.user.last_name}",
                        created_by=request.user.userprofile  # Assuming UserProfile is linked to User
                    )
                    success_count += 1
                    
                except Exception as e:
                    error_messages.append(f"Row {reader.line_num}: {str(e)}")
                    continue

            if error_messages:
                return render(request, 'transport/upload_vehicle.html', {
                    'warning': f"Processed {success_count} records successfully with some errors",
                    'detailed_errors': error_messages
                })
                
            return redirect('/table_vehicle/')
            
        except Exception as e:
            return render(request, 'transport/upload_vehicle.html', {
                'error': f"File processing error: {str(e)}"
            })

    return render(request, 'transport/upload_vehicle.html', {})
