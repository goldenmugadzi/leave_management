from django.shortcuts import render, redirect
from datetime import datetime
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
from it.users.models import Regions, Sections, Designations, UserProfile, CostCenter
from Asset_Register.models import ProductType, ZetdcAssets
from datetime import datetime
from dateutil import parser
from django.contrib import messages
from django.db import transaction,IntegrityError
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect  # Add get_object_or_404 here

#User = get_user_model()
def createAsset(request):
    if request.method == 'POST':
        form = ZetdcAssetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  
            return redirect('table_asset') 
        else:
        
            print(form.errors)  
    else:
        form = ZetdcAssetForm()

    return render(request, "asset_register/createAsset.html", {"form": form})

def show_asset(request):
    
    return render(request, 'asset_register/table_asset.html')

def table_asset (request):
  return render(request,'asset_register/table_asset.html')

def show_product (request):
  return render(request,'asset_register/table_product.html')

def show_asset_datatable(request):
    try:
        print("\n===== NEW REQUEST =====")
        print(f"Request: {request.GET}")

        # Get parameters with defaults
        try:
            draw = int(request.GET.get('draw', 1))
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', 10))
            search_value = request.GET.get('search[value]', '')
        except ValueError as e:
            return JsonResponse({'error': f'Invalid parameter: {str(e)}'}, status=400)

        # Get all assets without region filtering
        assets = ZetdcAssets.objects.all()
        print(f"DEBUG: Showing all assets, count: {assets.count()}")

        # Apply search filter
        if search_value:
            print(f"DEBUG: Applying search filter for: {search_value}")
            assets = assets.filter(
                Q(asset_state__icontains=search_value) |
                Q(product_type__product_type__icontains=search_value) |
                Q(serial_number__icontains=search_value) |
                Q(department__section__icontains=search_value) |
                Q(user__first_name__icontains=search_value) |
                Q(user__last_name__icontains=search_value) |
                Q(regions__region__icontains=search_value) |
                Q(purchase_cost__icontains=search_value) |
                Q(designation__description__icontains=search_value) |
                Q(model__icontains=search_value) |
                Q(warrant__icontains=search_value) |
                Q(created_by__icontains=search_value)
            )
            print(f"DEBUG: Post-search asset count: {assets.count()}")

        # Ordering
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')
        if order_column and order_dir:
            column_map = {
                "0": "id",
                "1": "asset_state",
                "2": "product_type__product_type",
                "3": "serial_number",
                "4": "department__section",
                "5": "user__first_name",
                "6": "regions__region",
                "7": "purchase_cost",
                "8": "designation__description",
                "9": "date_purchased",
                "10": "warrant",
                "11": "model",
                "12": "created_by",
                "13": "created_at",
                "14": "asset_number",
            }
            column_name = column_map.get(order_column)
            if column_name:
                order_prefix = '-' if order_dir == 'desc' else ''
                assets = assets.order_by(f'{order_prefix}{column_name}')
                print(f"DEBUG: Ordering by {order_prefix}{column_name}")

        # Pagination
        paginator = Paginator(assets, length)
        page_number = start // length + 1
        try:
            page_obj = paginator.get_page(page_number)
            print(f"DEBUG: Page {page_number} of {paginator.num_pages}")
        except Exception as e:
            print(f"DEBUG: Pagination error: {e}")
            page_obj = []

        # Prepare data - ensure all values are JSON serializable
        asset_list = []
        for asset in page_obj:
            print(asset.created_by)
            asset_data = {
                "id": asset.id,
                "asset_state": asset.asset_state,
                "asset_number": asset.asset_number,
                "product_type": asset.product_type.product_type if asset.product_type else None,
                "serial_number": asset.serial_number,
                "department": asset.department.section if asset.department else None,
                "user": f"{asset.user.first_name} {asset.user.last_name}" if asset.user else None,
                "regions": asset.regions.region if asset.regions else None,
                "purchase_cost": float(asset.purchase_cost) if asset.purchase_cost else 00.00,
                "designations": asset.designation.description if asset.designation else None,
                "date_purchased": asset.date_purchased.isoformat() if asset.date_purchased else None,
                "warrant": asset.warrant,
                "cost_center": asset.cost_center.name if asset.cost_center else None,
                "model": asset.model,
                "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
                "supplier": asset.supplier,
                "created_by": f"{asset.created_by.first_name} {asset.created_by.last_name}" if asset.created_by else None,
            }
            asset_list.append(asset_data)

        print(f"DEBUG: Returning {len(asset_list)} items")
        
        response = JsonResponse({
            'draw': draw,
            'recordsTotal': assets.count(),
            'recordsFiltered': assets.count(),
            'data': asset_list
        }, json_dumps_params={'ensure_ascii': False})
        
        
        response["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as ex:
        print(f"ERROR: {str(ex)}", exc_info=True)
        return JsonResponse({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(ex)
        }, status=500)
       
def update_asset(request, asset_id):
    asset = get_object_or_404(ZetdcAssets, id=asset_id)  

    if request.method == 'POST':
        form = ZetdcAssetForm(request.POST, instance=asset) 

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, "Asset updated successfully!")
                    return redirect('/table_asset/') 
            except Exception as e:
                messages.error(request, f"Error updating asset: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ZetdcAssetForm(instance=asset) 

    return render(request, 'asset_register/update_asset.html', {'form': form, 'asset': asset})

def create_product(request):
    if request.method == 'POST':
        print("request",request.POST )

        producttype = ProductType(
            id= request.POST['id'],
            product_type= request.POST['product_type'],
            code= request.POST['code'],
        )
            
        print("prod data: ", producttype)
        producttype.save()
        print("Data saved successfully!")
        #messages.success(request, "Fault created successfully!")
        
        return redirect('show_fault')
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
            created_users = set()
            duplicate_users = set()  

            for row_num, row in enumerate(reader, start=1):
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

                       # Replace the asset_state handling section with this:
                        asset_state = row.get('asset state', '').strip()
                        valid_states = dict(ZetdcAssets._meta.get_field('asset_state').choices)

                        # Convert empty string to None
                        asset_state = asset_state if asset_state else None

                        # Validate only if a value was provided
                        if asset_state is not None:
                            if asset_state not in valid_states:
                                raise ValueError(f"Invalid asset state: {asset_state}. Valid options are: {', '.join(valid_states.keys())}")

                        asset = ZetdcAssets(
                            product_type=product_type,
                            asset_state=asset_state,
                            serial_number=row.get('serial number', '').strip(),
                            user=user_profile,
                            date_purchased=parsed_date or date.today(),
                            department=section,
                            regions=region,
                            model=row.get('model', '').strip(),
                            #created_by=request.user.userprofile,
                            purchase_cost=row.get('purchase_cost', 0),
                            warrant=row.get('warrant', '') or None,
                            supplier=row.get('supplier', '') or None,
                        )
                        
                        asset.full_clean() 
                        asset.save()
                        success_count += 1

                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
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
                return redirect('/table_asset/')
            
            return render(request, 'asset_register/upload_asset.html', {
                'error': "No assets were imported",
                'error_count': len(error_messages),
                'detailed_errors': error_messages[:20],
                'created_users': sorted(created_users),
                'duplicate_users': sorted(duplicate_users),
            })
            
        except Exception as e:
            return render(request, 'asset_register/upload_asset.html', {
                'error': f"File processing error: {str(e)}"
            })

    return render(request, 'asset_register/upload_asset.html', {})



