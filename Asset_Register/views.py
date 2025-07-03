from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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


@login_required
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

@login_required
def table_asset (request):
  return render(request,'asset_register/table_asset.html')

@login_required
def table_hr (request):
  return render(request,'asset_register/table_hr.html')

@login_required
def tab (request):
  return render(request,'asset_register/tab.html')

@login_required
def show_table (request):
  return render(request,'asset_register/table_hr.html')

@login_required
def show_product (request):
  return render(request,'asset_register/table_product.html')

@login_required
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
            'asset_type': 'asset',
            'product_type': instance.product_type,
            'serial_number': instance.serial_number,
            'assetnumber': instance.asset_number,
            'asset_state': instance.asset_state,
            'user': instance.user,
            'regions': instance.regions,
            'purchase_cost': instance.purchase_cost,
            'designation': instance.designation,
            'department': instance.department,
            'date_purchased': instance.date_purchased,
            'model': instance.model,
            'warrant': instance.warrant,
            'cost_center': instance.cost_center,
            #'created_by': instance.created_by,
            'supplier': instance.supplier,
        }
    elif asset_type == 'hr':
        instance = get_object_or_404(HumanResource, id=asset_id)
        initial = {
            'asset_type': 'hr',
            'assetnumber': instance.assetnumber,
            'designation': instance.designation,
            'cost_center': instance.cost_center,
            'department': instance.department,
            'officenumber': instance.officenumber,
            'asset_state': instance.assetstate,
            'regions': instance.regions,
            'descriptionofitem': instance.descriptionofitem,
            'user': instance.user,
            'lastchecked_at': instance.lastchecked_at,
        }
    else:
        return render(request, '404.html', status=404)

    if request.method == 'POST':
        form = CombinedAssetForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            if asset_type == 'asset':
                instance.product_type = cleaned['product_type']
                instance.serial_number = cleaned['serial_number']
                instance.asset_number = cleaned['assetnumber']
                instance.asset_state = cleaned['asset_state']
                instance.user = cleaned['user']
                instance.regions = cleaned['regions']
                instance.purchase_cost = cleaned['purchase_cost'] or 0
                instance.designation = cleaned['designation']
                instance.department = cleaned['department']
                instance.date_purchased = cleaned['date_purchased']
                instance.model = cleaned['model']
                instance.warrant = cleaned['warrant']
                instance.cost_center = cleaned['cost_center']
                #instance.created_by = cleaned['created_by']
                instance.supplier = cleaned['supplier']
            else:
                instance.assetnumber = cleaned['assetnumber']
                instance.designation = cleaned['designation']
                instance.cost_center = cleaned['cost_center']
                instance.department = cleaned['department']
                instance.officenumber = cleaned['officenumber']
                instance.assetstate = cleaned['asset_state']
                instance.regions = cleaned['regions']
                instance.descriptionofitem = cleaned['descriptionofitem']
                instance.user = cleaned['user']
                instance.lastchecked_at = cleaned['lastchecked_at'] or None
            instance.save()
            messages.success(request, "Asset updated successfully!")
            return redirect('/tab/')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CombinedAssetForm(initial=initial)

    template = 'asset_register/update_asset.html' if asset_type == 'asset' else 'asset_register/update_hr_asset.html'
    return render(request, template, {'form': form, 'asset': instance})

@login_required
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

@login_required
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

@login_required
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

@login_required
def show_report(request):
    
    return render(request, 'asset_register/asset_report.html')

@login_required
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

@login_required
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

@login_required
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
            created_users = set()
            duplicate_users = set()  

            for row_num, row in enumerate(reader, start=1):
                print(f"Processing row {row_num}: {row}")
                try:
                    with transaction.atomic():
                        # Parse date
                        date_string = row.get('date purchased', '').strip()
                        parsed_date = None
                        
                        if date_string:
                            try:
                                parsed_date = datetime.strptime(date_string, "%A, %B %d, %Y").date()
                            except ValueError:
                                try:
                                    parsed_date = datetime.strptime(date_string, "%d-%b-%y").date()
                                except ValueError:
                                    raise ValueError("Invalid date format")

                        product_type, _ = ProductType.objects.get_or_create(
                            product_type=row.get('product type', '').strip())
                        
                        row = {k.lower(): v for k, v in row.items()}
                        section_name = row.get('section', '').strip()
                        if not section_name:
                            raise ValueError("Section is required")
                        section, _ = Sections.objects.get_or_create(section=section_name)

                        region_name = row.get('region', '').strip()
                        if not region_name:
                            raise ValueError("Region is required")
                        region, _ = Regions.objects.get_or_create(region=region_name)

                        username = row.get('user', '').strip()
                        if not username:
                            raise ValueError("User is required")
                        
                        name_parts = username.split()
                        first_name = name_parts[0] if len(name_parts) > 0 else username
                        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                        
                        try:
                            user_profile, created = UserProfile.objects.get_or_create(
                                username=username[:150],  
                                defaults={
                                    'first_name': first_name[:30],
                                    'last_name': last_name[:30],
                                    'email': f"{username.lower().replace(' ', '.')[:50]}@example.com",
                                }
                            )
                            
                            if created:
                                created_users.add(username)
                                
                        except IntegrityError:
                            duplicate_users.add(username)
                            raise ValueError(f"Username '{username}' already exists (truncated)")

                       
                        asset_state = row.get('asset state', '').strip()
                        valid_states = dict(ZetdcAssets._meta.get_field('asset_state').choices)

                        if not asset_state:
                            asset_state = 'Awaiting New User'
                        if asset_state not in valid_states:
                            raise ValueError(f"Invalid asset state: {asset_state}. Valid options are: {', '.join(valid_states.keys())}")

                        asset = ZetdcAssets(
                            product_type=product_type,
                            asset_state=asset_state,
                            serial_number=row.get('serial number', '').strip(),
                            asset_number=row.get('asset number', '').strip(),
                            user=user_profile,
                            date_purchased=parsed_date or date.today(),
                            department=section,
                            regions=region,
                            model=row.get('model', '').strip(),
                            purchase_cost=row.get('purchase_cost', 0),
                            warrant=row.get('warrant', '') or None,
                            supplier=row.get('supplier', '') or None,
                            
                        )
                        
                        asset.full_clean() 
                        asset.save()
                        success_count += 1

                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    print(error_msg)  # <--- Add this line
                    if "duplicate" in str(e).lower():
                        duplicate_users.add(username)
                        error_msg = f"Row {row_num}: User '{username}' already exists"
                    error_messages.append(error_msg)
                    continue

            if success_count > 0:
                messages.success(request, f"Successfully imported {success_count} assets")
                if created_users:
                    messages.info(request, f"Created {len(created_users)} new user profiles")
                if duplicate_users:
                    messages.warning(request, f"Skipped {len(duplicate_users)} duplicate users")
                return redirect('/tab/')
            
            return render(request, 'asset_register/upload_asset.html', {
                'error': "No assets were imported",
                'error_count': len(error_messages),
                'detailed_errors': error_messages[:20],
                'created_users': sorted(created_users),
                'duplicate_users': sorted(duplicate_users),
            })
            
        except Exception as e:
            print("Outer exception:", str(e))
            return render(request, 'asset_register/upload_asset.html', {
                'error': f"File processing error: {str(e)}"
            })

    return render(request, 'asset_register/upload_asset.html', {})

@login_required
def combined_assets_datatable(request):
    
    try:
        print("\n===== NEW REQUEST =====")
        print(f"User: {request.user.first_name} {request.user.last_name} ({request.user.username})")

        assets_qs = []
        assets = ZetdcAssets.objects.all()
        print(f"assets count: {assets.count()}")
        
        hr = HumanResource.objects.all()

    
        cost_centers = request.user.cost_centers_for(["IT Asset Register"])
        if cost_centers:
            print(f"Filtering by cost centers: {cost_centers}")
            assets = assets.filter(cost_center__in=cost_centers)
            print(f"After cost center filtering: {assets.count()}")
        else:
            descendents = request.user.cost_center_and_decendace()
            print(f"Filtering by cost center descendents: {descendents}")
            assets = assets.filter(cost_center__in=descendents)
            print(f"After descendents filtering: {assets.count()}")
    
    
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        department_filter = request.GET.get('department', '')

        # assets_qs = ZetdcAssets.objects.all()
        # hr_qs = HumanResource.objects.all()
        

        # Filtering by search
        if search_value:
            assets_qs = assets.filter(
                Q(product_type__product_type__icontains=search_value) |
                Q(asset_state__icontains=search_value) |
                Q(asset_number__icontains=search_value) |
                Q(serial_number__icontains=search_value) |
                Q(user__first_name__icontains=search_value) |
                Q(user__last_name__icontains=search_value) |
                Q(department__section__icontains=search_value) |
                Q(regions__region__icontains=search_value)
            )
            hr_qs = hr.filter(
                Q(descriptionofitem__icontains=search_value) |
                Q(assetnumber__icontains=search_value) |
                Q(assetstate__icontains=search_value) |
                Q(user__first_name__icontains=search_value) |
                Q(user__last_name__icontains=search_value) |
                Q(department__section__icontains=search_value) |
                Q(regions__region__icontains=search_value)
            )

        # Filtering by department (optional)
        if department_filter:
            assets_qs = assets.filter(department__section__icontains=department_filter)
            hr_qs = hr.filter(department__section__icontains=department_filter)

        # Build asset list
        print("total",assets)
        assets_list = [{
            "id": a.id,
            "product_type": a.product_type.product_type if a.product_type else "",
            "descriptionofitem": "", 
            "asset_state": a.asset_state,
            "asset_number": a.asset_number,
            "serial_number": a.serial_number if hasattr(a, "serial_number") else "",
            "user": f"{a.user.first_name} {a.user.last_name}" if a.user else "",
            "officenumber": "",  
            "department": a.department.section if a.department else "",
            "regions": a.regions.region if a.regions else "",
            "designation": a.designation.description if a.designation else "",
            "lastchecked_at": "",  
            "cost_center": a.cost_center.name if a.cost_center else "",
            "model": a.model if hasattr(a, "model") else "",
        } for a in assets]
        

        #Build HR list
        hr_list = [{
            "id": h.id,
            "product_type": "", 
            "descriptionofitem": h.descriptionofitem if h.descriptionofitem else "",
            "asset_state": h.assetstate,
            "asset_number": h.assetnumber,
            "serial_number": "", 
            "user": f"{h.user.first_name} {h.user.last_name}" if h.user else "",
            "officenumber": h.officenumber if h.officenumber else "",
            "department": h.department.section if h.department else "",
            "regions": h.regions.region if h.regions else "",
            "designation": h.designation.description if h.designation else "",
            "lastchecked_at": h.lastchecked_at.strftime('%Y-%m-%d') if h.lastchecked_at else "",
            "cost_center": h.cost_center.name if h.cost_center else "",
            "model": "", 
        } for h in hr]

        combined = assets_list
        combined_sorted = sorted(combined, key=lambda x: x['id'], reverse=True)
        total = len(combined_sorted)
        paginated = combined_sorted[start:start+length]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": total,
            "data": paginated
        })
    except Exception as ex:
        print("Combined datatable error:", ex)
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(ex)
        }, status=500)
        
@login_required
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



