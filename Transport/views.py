from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from.models import TransportAssets,Tyres, Battery, Allocation, TripRecord
import json
import csv
from django.http import HttpResponse
from datetime import date, datetime 
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.urls import reverse
from django.template.loader import render_to_string
from.models import*
from it.users.models import Regions, Sections, UserProfile,Designations,CostCenter
from.forms import  TripRecordForm, TripDetailsForm,TyresForm, BatteryForm, AllocationForm
from django.shortcuts import render, redirect

@login_required
def register_vehicle(request):
   if request.method == 'POST':
        form =  TripRecordForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  
            return redirect('table_vehicle') 
        else:
        
            print(form.errors)  
   else:
        form = TripRecordForm()

   return render(request, "transport/register_vehicle.html", {"form": form})

def table_vehicle (request):
  return render(request,'transport/table_vehicle.html')

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

def vehicle_datatable(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    
    print("=== DATATABLE REQUEST ===")
    print("draw:", draw, "start:", start, "length:", length, "search_value:", search_value)

    qs = TripRecord.objects.select_related(
        "vehicle_details", "drivers_name", "region", "department", "depot", "cost_center"
    )
    
    print("Initial QS count:", qs.count())
    
    if search_value:
        qs = qs.filter(
            Q(details_of_journey__icontains=search_value) |
            Q(defects_and_repairs_carried_out__icontains=search_value)
        )
        print("Filtered QS count after search:", qs.count())

    total = TripRecord.objects.count()
    filtered = qs.count() 
    print("Total records:", total, "Filtered records:", filtered)

    qs = qs.order_by('-id')[start:start+length]
    print("QS after pagination:", qs.count())

    data = []
    for triprecord in qs:
        vehicle_str = f"{triprecord.vehicle_details.fleet_number} / {triprecord.vehicle_details.make} / {triprecord.vehicle_details.reg_number}" if triprecord.vehicle_details else ""
        driver_str = str(triprecord.drivers_name) if triprecord.drivers_name else ""
        data.append({
            "id": triprecord.id,
            "date": triprecord.date.strftime("%Y-%m-%d %H:%M") if triprecord.date else "",
            "depot": str(triprecord.depot) if triprecord.depot else "",
            "vehicle_details": vehicle_str,
            "drivers_name": driver_str,
            "opening_speedo_reading": triprecord.opening_speedo_reading,
            "closing_speedo_reading": triprecord.closing_speedo_reading,
            "trip_distance": triprecord.trip_distance,
            "region": str(triprecord.region) if triprecord.region else "",
            "department": str(triprecord.department) if triprecord.department else "",
            "allocation_code": triprecord.allocation_code,
            "cost_center": str(triprecord.cost_center) if triprecord.cost_center else "",
            "fuel_drawn": triprecord.fuel_drawn,
            "oil_drawn": triprecord.oil_drawn,
            "place_drawn": triprecord.place_drawn,
            "details_of_journey": triprecord.details_of_journey,
            "defects_and_repairs_carried_out": triprecord.defects_and_repairs_carried_out,
        })
    
    print("Prepared data length:", len(data))
    print("Sample data:", data[:1] if data else "No data")

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data
    })


def vehicle_dashboard (request):
  return render(request,'transport/vehicle_dashboard.html')

def add_trip(request):
    if request.method == "POST":
        form = TripDetailsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("trip_list") 
    else:
        form = TripDetailsForm()
    return render(request, "transport/trip.html", {"form": form})

def trip_list(request):
    return render(request, 'transport/trip_table.html')

def trip_datatable(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs = TripRecord.objects.all()

    # Search filtering
    if search_value:
        qs = qs.filter(
            Q(vehicle_details__icontains=search_value) |
            Q(drivers_name__username__icontains=search_value) |
            Q(stf_number__icontains=search_value) |
            Q(details_of_journey__icontains=search_value)
        )

    total = qs.count()
    qs = qs.order_by('-date')[start:start+length]

    data = []
    for trip in qs:
        vehicle_str = f"{trip.vehicle_details.fleet_number} / {trip.vehicle_details.make} / {trip.vehicle_details.reg_number}" if trip.vehicle_details else ""
        data.append({
            "vehicle_details": vehicle_str,
            "driver": str(trip.drivers_name) if trip.drivers_name else "",
            "date": trip.date.strftime("%Y-%m-%d %H:%M"),
            "allocation_code": trip.allocation_code,
            "opening_speedo_reading": trip.opening_speedo_reading,
            "closing_speedo_reading": trip.closing_speedo_reading,
            "details_of_journey": trip.details_of_journey,
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })

def vehicle_datatables(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs = TransportAssets.objects.all()

    # Search filter
    if search_value:
        qs = qs.filter(
            Q(reg_number__icontains=search_value) |
            Q(fleet_number__icontains=search_value) |
            Q(make__icontains=search_value) |
            Q(model__icontains=search_value) |
            Q(year__icontains=search_value) |
            Q(fuel_type__icontains=search_value)
        )

    total = qs.count()
    qs = qs.order_by('-id')[start:start+length]

    data = []
    for asset in qs:
        data.append({
            "reg_number": asset.reg_number,
            "fleet_number": asset.fleet_number,
            "make": asset.make,
            "model": asset.model,
            "year": asset.year,
            "fuel_drawn": asset.fuel_drawn,
            "oil_drawn": asset.oil_drawn,
            "fuel_type": asset.fuel_type,
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })

def vehicle_list(request):
    return render(request, 'transport/details.html')

def tyres_list(request):
    return render(request, 'transport/tyres.html')

def battery_list(request):
    return render(request, 'transport/battery.html')

def allocation_list(request):
    return render(request, 'transport/allocation.html')


def add_tyres(request):
    if request.method == "POST":
        form = TyresForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("tyres") 
    else:
        form = TyresForm()
    return render(request, "transport/add_tyres.html", {"form": form})


def add_battery(request):
    if request.method == "POST":
        form = BatteryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("batteries")
    else:
        form = BatteryForm()
    return render(request, "transport/add_battery.html", {"form": form})


def add_allocation(request):
    if request.method == "POST":
        form = AllocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("allocations")
    else:
        form = AllocationForm()
    return render(request, "transport/add_allocations.html", {"form": form})