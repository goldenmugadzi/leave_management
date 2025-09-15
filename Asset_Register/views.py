from django.shortcuts import render, redirect
from datetime import datetime, date
from django.core.paginator import Paginator
from django.http import JsonResponse
import json, os
from django.conf import settings
#from django.contrib.auth import get_user_model
from django.db.models import Q
import csv
from django.http import HttpResponse
from .forms import *
from dateutil import parser
from it.users.models import Regions, Sections, Designations, UserProfile, CostCenter,Roles
from Asset_Register.models import ProductType, ZetdcAssets
from datetime import datetime
from dateutil import parser
from django.contrib import messages
from django.db import transaction,IntegrityError
import traceback
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect  # Add get_object_or_404 here

#User = get_user_model()
def create_asset(request):
    if request.method == 'POST':
        form = CombinedAssetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('tab')  
        else:
            print(form.errors)
    else:
        form = CombinedAssetForm()

    return render(request, "asset_register/create_asset.html", {"form": form})


def show_asset(request):
    try:
        user_roles = request.user.get_user_role_for_application("IT Asset Register")
        is_technician = user_roles.name == 'technician'
    except AttributeError as e:
        print(f"Role error: {e}")
        is_technician = False

    return render(request, 'asset_register/table_asset.html', {
        'is_technician': is_technician
    })

def table_asset (request):
  return render(request,'asset_register/table_asset.html')

def table_hr (request):
  return render(request,'asset_register/table_hr.html')

def tab (request):
  return render(request,'asset_register/tab.html')

def show_table (request):
  return render(request,'asset_register/table_hr.html')

def show_product (request):
  return render(request,'asset_register/table_product.html')

def show_hr_datatable(request):
    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        humanresource = HumanResource.objects.all()

        if search_value:
            humanresource = humanresource.filter(
                Q(descriptionofitem__icontains=search_value) |
                Q(assetnumber__icontains=search_value) |
                Q(assetstate__icontains=search_value) |
                Q(user__icontains=search_value) |
                Q(officenumber__icontains=search_value) |
                Q(lastchecked_at__icontains=search_value) |
                Q(department__icontains=search_value)
            )

        total = humanresource.count()

        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column is not None and order_dir is not None:
            column_map = {
                "0": "descriptionofitem",
                "1": "assetnumber",
                "2": "assetstate",
                "3": "user",
                "4": "officenumber",
                "5": "department",
                "6": "regions",
                "7": "designation",
                "8": "lastchecked_at",
                "9": "cost_center",
            }

            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}'
                humanresource = humanresource.order_by(column_name)

        paginator = Paginator(humanresource, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)

        data = []
        for hr in page_obj:
            o = {
                "id": hr.id,
                "descriptionofitem": hr.descriptionofitem,
                "assetnumber": hr.assetnumber,
                "assetstate": hr.assetstate,
                "user": f"{hr.user.first_name} {hr.user.last_name}" if hr.user else None,
                "officenumber": hr.officenumber,
                "department": hr.department.section if hr.department else None,
                "regions": hr.regions.region if hr.regions else None,
                "designation": hr.designation.description if hr.designation else None,
                "lastchecked_at": hr.lastchecked_at,
                "cost_center": hr.cost_center.name if hr.cost_center else None,
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
    if not request.user.department == 'Human Resource':
        return JsonResponse({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })


def update_asset(request, asset_type, asset_id):
    if asset_type == 'asset':
        instance = get_object_or_404(ZetdcAssets, id=asset_id)
        initial = {
            'product_type': instance.product_type,
            'asset_state': instance.asset_state,
            'asset_number': instance.asset_number,
            'serial_number': instance.serial_number,
            'user': instance.user,
            'department': instance.department,
            'designation': instance.designation,
            'cost_center': instance.cost_center,
            'model': instance.model,
            'date_purchased': instance.date_purchased,
            #'supplier': instance.supplier,
            'warrant': instance.warrant,
        }
    elif asset_type == 'hr':
        instance = get_object_or_404(HumanResource, id=asset_id)
        initial = {
            'asset_number': instance.assetnumber,
            'designation': instance.designation,
            'cost_center': instance.cost_center,
            'department': instance.department,
            'user': instance.user,
            'model': instance.model,
            'date_purchased': instance.date_purchased,
            #'supplier': instance.supplier,
            'warrant': instance.warrant,
        }
    else:
        return render(request, '404.html', status=404)
    if request.method == 'POST':
        form = CombinedAssetForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Asset updated successfully!")
            return redirect('/tab/')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CombinedAssetForm(initial=initial, instance=instance)
    template = 'asset_register/update_asset.html' if asset_type == 'asset' else 'asset_register/update_hr_asset.html'
    return render(request, template, {'form': form, 'asset': instance})

def create_product(request):
    if request.method == 'POST':
        print("request",request.POST )

        producttype = ProductType(
            id= request.POST['id'],
            product_type= request.POST['product_type'],
            model= request.POST['model'],
        )
            
        print("prod data: ", producttype)
        producttype.save()
        print("Data saved successfully!")
        #messages.success(request, "Fault created successfully!")
        
        return redirect('table_product')
    return render(request, 'asset_register/create_product.html',{})

def show_product_datatable(request):
    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        product = ProductType.objects.all()

        if search_value:
            product = product.filter(
                product_type__icontains=search_value
            ) | product.filter(
                code__icontains=search_value
            )

        total = product.count()

        # Sorting
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column is not None and order_dir is not None:
            column_map = {
                "0": "id",
                "1": "product_type",
                "2": "model",
            }

            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}' 
                product = product.order_by(column_name)

        # Pagination
        paginator = Paginator(product, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)

        product_list = []
        for p in page_obj:
            asset = ZetdcAssets.objects.filter(product_type=p).first()  
            model = asset.model if asset else '' 

            new_product = {
                "id": p.id,
                "product_type": p.product_type,
                "model": model,
            }
            product_list.append(new_product)

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': product_list
        })

    except Exception as ex:
        print(ex)
        return JsonResponse({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

def update_product(request, id):
    producttype= ProductType.objects.filter(id=id).first()
    if request.method == 'POST':
        print("request",request.POST)
        #form.save()
        
        producttype.id = request.POST['id']
        producttype.product_type = request.POST['product_type']
        producttype.code = request.POST['code']

        producttype.save()
        return redirect('/table_product')
        
    return render(request,'asset_register/updateproduct.html',{'producttype':producttype}) 

def show_report(request):
    
    return render(request, 'asset_register/asset_report.html')

def show_report_datatable(request):
    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        assets = ZetdcAssets.objects.all()
        print("assets ", assets)

        status_filter = request.GET.get('status')
        station_filter = request.GET.get('station')
        pick_station_filter = request.GET.get('pickStation')
        start_date_filter = request.GET.get('start_date')
        end_date_filter = request.GET.get('end_date')

        if status_filter and status_filter != "Select Status":
            print("status: ", status_filter)
            assets = assets.filter(asset_state=status_filter)
            print("assets: ", assets)
        if station_filter and station_filter != "Select Station":
            assets = assets.filter(department=station_filter)
        if pick_station_filter:  
            assets = assets.filter(regions=pick_station_filter)
        if start_date_filter:
            assets = assets.filter(date_purchased__gte=start_date_filter)
        if end_date_filter:
            assets = assets.filter(date_purchased__lte=end_date_filter)


        if search_value:
            assets = assets.filter(
                Q(asset_state__icontains=search_value) |
                Q(product_type__product_type__icontains=search_value) |
                Q(sections__section__icontains=search_value) |
                Q(regions__region__icontains=search_value) |
                Q(purchase_cost__icontains=search_value)
            )

        # Total number of records before filtering
        total = assets.count()

        # Sorting
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column is not None and order_dir is not None:
            column_map = {
                "0": "id",
                "1": "asset_state",
                "2": "product_type__product_type",
                "3": "sections__section",
                "4": "regions__region",
                "5": "date_purchased",
            }

            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}'  # Add descending order prefix
                assets = assets.order_by(column_name)

        # Pagination
        paginator = Paginator(assets, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)

        # Process assets
        asset_list = []
        for asset in page_obj:
            asset_dict = {
                "id": asset.id,
                "asset_state": asset.asset_state,
                "product_type": asset.product_type.product_type if asset.product_type else None,
                "department": asset.department.section if asset.department else None,
                "regions": asset.regions.region if asset.regions else None,
                "date_purchased": asset.date_purchased,
            }
            asset_list.append(asset_dict)

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': asset_list
        })
    except Exception as ex:
        print(ex)
        return JsonResponse({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

def export_csv(request):
    # Get filter parameters from the request
    asset_state = request.GET.get('status', None)
    sections = request.GET.get('sections', None)
    regions = request.GET.get('regions', None)
    pick_station = request.GET.get('pickStation', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    assets = ZetdcAssets.objects.all()  


    if asset_state and asset_state != 'Select Status':
        assets = assets.filter(asset_state=asset_state)
    
    if sections:
        assets = assets.filter(sections=sections)
       
    if regions:
        assets = assets.filter(regions=regions)
        
    if pick_station:
        assets = assets.filter(pick_station=pick_station)
      
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        assets = assets.filter(date_purchased__gte=start_date)
       
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        assets = assets.filter(date_purchased__lte=end_date)
       

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Assets.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Product Type', 'Asset State', 'Department', 'Regions', 'Date Purchased'])

    if not assets.exists():
        writer.writerow(['No data found'])
    for asset in assets:
            asset_state_name = asset.asset_state if asset.asset_state else 'N/A'
            section_name = asset.sections if asset.sections else 'N/A'
            region_name = asset.regions if asset.regions else 'N/A'

            # Write the row to the CSV
            writer.writerow([
                asset.id,
                asset.product_type,
                asset_state_name,  
                section_name,      
                region_name,       
                asset.date_purchased
            ])
    return response

def upload_asset(request):
    if request.method == 'POST':
        csvfile = request.FILES.get('uploaded_csv')
        if not csvfile:
            return render(request, 'asset_register/upload_asset.html', {'error': 'No file uploaded'})

        try:
            decoded_file = csvfile.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            success_count = 0
            error_messages = []

            for row_num, row in enumerate(reader, start=1):
                print(f"Processing row {row_num}: {row}")
                try:
                    with transaction.atomic():
                        # Normalize keys and convert empty strings to None
                        row = {k.lower(): (v.strip() if v.strip() else None) for k, v in row.items()}

                        # Parse date
                        parsed_date = None
                        if row.get('date purchased'):
                            try:
                                parsed_date = datetime.strptime(row['date purchased'], "%A, %B %d, %Y").date()
                            except ValueError:
                                try:
                                    parsed_date = datetime.strptime(row['date purchased'], "%d-%b-%y").date()
                                except ValueError:
                                    parsed_date = None

                        # Use get_or_create for all fields that may exist or be duplicated
                        product_type, _ = ProductType.objects.get_or_create(product_type=row.get('product type') or 'Unknown')
                        section, _ = Sections.objects.get_or_create(section=row.get('section') or 'Unknown')
                        designation_name = row.get('designation') or 'Unknown'
                        designation = Designations.objects.filter(description=designation_name).first()
                        if not designation:
                            # Create a new one if it doesn't exist
                            designation = Designations.objects.create(description=designation_name)
                        region, _ = Regions.objects.get_or_create(region=row.get('region') or 'Unknown')
                        # Handle cost center safely
                        cost_center_name = row.get('cost center')
                        cost_center_code = row.get('cost center code') or ''
                        parent_cost_center = None

                        # Validate cost center name
                        valid_cost_centers = set(CostCenter.objects.values_list('name', flat=True))
                        if not cost_center_name or cost_center_name not in valid_cost_centers:
                            cost_center_name = 'IT'
                        cost_center, created = CostCenter.objects.get_or_create(
                            name=cost_center_name,
                            defaults={
                                'id': uuid.uuid4().hex[:20],
                                'code': cost_center_code,
                                'parent': parent_cost_center
                            }
                        )

                        # User: only existing, else None
                        user_profile = None
                        if row.get('user'):
                            user_profile = UserProfile.objects.filter(username=row['user']).first()

                        # Asset state default
                        asset_state = row.get('asset state') or 'Awaiting New User'
                        valid_states = dict(ZetdcAssets._meta.get_field('asset_state').choices)
                        if asset_state not in valid_states:
                            asset_state = 'Awaiting New User'

                        # Create asset
                        asset = ZetdcAssets(
                            product_type=product_type,
                            asset_state=asset_state,
                            serial_number=row.get('serial number'),
                            asset_number=row.get('asset number'),
                            user=user_profile,
                            date_purchased=parsed_date or date.today(),
                            department=section,
                            designation=designation,
                            regions=region,
                            model=row.get('model'),
                            #purchase_cost=row.get('purchase_cost') or 0,
                            warrant=row.get('warrant'),
                            supplier=row.get('supplier'),
                            cost_center=CostCenter.objects.filter(id=142).first(),
                        )
                        # Skip full_clean() to allow duplicates
                        asset.save()
                        success_count += 1

                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    print(error_msg)
                    error_messages.append(error_msg)
                    continue

            if success_count > 0:
                messages.success(request, f"Successfully imported {success_count} assets")
                return redirect('/tab/')

            return render(request, 'asset_register/upload_asset.html', {
                'error': "No assets were imported",
                'error_count': len(error_messages),
                'detailed_errors': error_messages[:20],
            })

        except Exception as e:
            print("Outer exception:", e)
            return render(request, 'asset_register/upload_asset.html', {'error': f"File processing error: {e}"})

    return render(request, 'asset_register/upload_asset.html', {})


import uuid
from django.http import JsonResponse
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder

def combined_assets_datatable(request):
    try:
        print("\n===== NEW REQUEST =====")
        print(f"User: {request.user.first_name} {request.user.last_name} ({request.user.username})")

        # Start with ZetdcAssets queryset
        assets = ZetdcAssets.objects.select_related(
            "product_type", "user", "department", "regions", "designation", "cost_center"
        ).all()

        print(f"Initial assets count: {assets.count()}")

        # Apply cost center restrictions
        cost_centers = request.user.cost_centers_for(["IT Asset Register"])
        if cost_centers:
            print(f"Filtering by cost centers: {cost_centers}")
            assets = assets.filter(cost_center__in=cost_centers)
        else:
            descendents = request.user.cost_center_and_decendace()
            print(f"Filtering by cost center descendents: {descendents}")
            assets = assets.filter(cost_center__in=descendents)

        print(f"After filtering: {assets.count()}")

        # DataTables request params
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")
        department_filter = request.GET.get("department", "")

        # Apply search filter
        if search_value:
            assets = assets.filter(
                Q(product_type__product_type__icontains=search_value) |
                Q(asset_state__icontains=search_value) |
                Q(asset_number__icontains=search_value) |
                Q(serial_number__icontains=search_value) |
                Q(user__first_name__icontains=search_value) |
                Q(user__last_name__icontains=search_value) |
                Q(department__section__icontains=search_value) |
                Q(regions__region__icontains=search_value) |
                Q(designation__designation__icontains=search_value) |
                Q(cost_center__cost_center__icontains=search_value) |
                Q(model__icontains=search_value)
            )

        # Apply department filter
        if department_filter:
            assets = assets.filter(department__section__icontains=department_filter)

        # Build asset list (fields aligned with CSV upload)
        assets_list = []
        for a in assets:
            assets_list.append({
                "id": a.id,
                "product_type": a.product_type.product_type if a.product_type else "",
                "asset_state": a.asset_state or "",
                "asset_number": a.asset_number or "",
                "serial_number": a.serial_number or "",
                "user": f"{a.user.first_name} {a.user.last_name}" if a.user else "",
                "section": a.department.section if a.department else "",
                "region": a.regions.region if a.regions else "",
                "designation": a.designation.description if a.designation else "",
                "cost_center": a.cost_center.name if a.cost_center else "",
                "model": a.model or "",
                "date_purchased": a.date_purchased.strftime("%Y-%m-%d") if a.date_purchased else "",
                #"purchase_cost": str(a.purchase_cost) if a.purchase_cost else "0.00",
                "supplier": a.supplier or "",
                "warrant": a.warrant or "",
            })

        # Sorting & pagination
        combined_sorted = sorted(assets_list, key=lambda x: x["id"], reverse=True)
        total = len(combined_sorted)
        paginated = combined_sorted[start:start+length]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": total,
            "data": paginated,
        }, encoder=DjangoJSONEncoder)

    except Exception as ex:
        print("Combined datatable error:", ex)
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(ex),
        }, status=500)

        
def show_combined_assets(request):
    try:
        user_roles = request.user.get_user_role_for_application("IT Asset Register")
        is_technician = user_roles.name == 'technician'
    except AttributeError as e:
        print(f"Role error: {e}")
        is_technician = False
        
    return render(request, 'asset_reqister/table_assets.html', {
        'is_technician': is_technician,
    })

def asset_state_chart_data(request):
    # Group by region and department, count asset states
    from django.db.models import Count

    data = (
        ZetdcAssets.objects
        .values('regions__region', 'department__section', 'asset_state')
        .annotate(count=Count('id'))
        .order_by('regions__region', 'department__section', 'asset_state')
    )

    # Organize data for Chart.js
    chart = {}
    for row in data:
        region = row['regions__region'] or "Unknown"
        department = row['department__section'] or "Unknown"
        asset_state = row['asset_state'] or "Unknown"
        key = f"{region} - {department}"
        if key not in chart:
            chart[key] = {}
        chart[key][asset_state] = row['count']

    # Prepare labels and datasets
    labels = list(chart.keys())
    all_states = set()
    for states in chart.values():
        all_states.update(states.keys())
    all_states = sorted(all_states)

    datasets = []
    for state in all_states:
        datasets.append({
            "label": state,
            "data": [chart[label].get(state, 0) for label in labels],
        })

    return JsonResponse({
        "labels": labels,
        "datasets": datasets,
    })

def download_asset_template(request):
    content = (
        "ID,Product Type,Asset State,Asset Number,Serial Number,User,Section,Region,Designation,Cost Center,Model\n"
    )
    response = HttpResponse(content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="asset_template.csv"'
    return response



