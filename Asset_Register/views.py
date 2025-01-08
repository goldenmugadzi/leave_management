from django.shortcuts import render, redirect
from datetime import datetime
from django.core.paginator import Paginator
from django.http import JsonResponse
import json, os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
import csv
from django.http import HttpResponse

from Asset_Register.models import Designations, ProductType, Regions, Sections, ZetdcAssets

User = get_user_model()

def create_asset(request):
    url_path = request.path.split("/")
    if request.method == 'POST':
        product_type = request.POST['product_id']
        asset_state = request.POST['asset_state']
        serial_number = request.POST['serial_number']
        asset_number = request.POST['asset_number']
        department = request.POST['department']
        user = request.POST['user']
        regions = request.POST['regions']
        purchase_cost = request.POST['purchase_cost']
        designations = request.POST['designations']
        date_purchased = request.POST['date_purchased']
        warrant = request.POST['warrant']
        model = request.POST['model']

        pd = ProductType.objects.filter(id=product_type).first()
        rg = Regions.objects.filter(id=regions).first()
        ds = Designations.objects.filter(id=designations).first()
        dp = Sections.objects.filter(id=department).first()
        sr = User.objects.filter(id=user).first()

        um = ZetdcAssets(
            asset_state= asset_state,
            product_type= pd if pd else None,
            serial_number = serial_number,
            asset_number= asset_number,
            department = dp if dp else None,
            user=sr,
            regions= rg if rg else None,
            purchase_cost=purchase_cost,
            designations=ds if ds else None,
            date_purchased=date_purchased,
            warrant=warrant,
            model=model,
            created_at = datetime.now().date(),
            updated_at = datetime.now().date(),
            created_by = "Goldy",
        )
        um.save()

        return render(request, 'asset_register/create_asset.html', {
                      "url_path": url_path
                      })
    
    regions=Regions.objects.all()
    
    sections=Sections.objects.all()
    designation=Designations.objects.all()
    
    users=User.objects.all()
    print('user', users)
    product_type=ProductType.objects.all()
    return render(request, 'asset_register/create_asset.html', {"url_path": url_path, 'regions': regions, 'sections': sections, 'designations': designation, 'product_types':product_type, 'users': users})


def show_asset(request):
    
    return render(request, 'asset_register/table_asset.html')

def table_asset (request):
  return render(request,'asset_register/table_asset.html')

def show_product (request):
  return render(request,'asset_register/table_product.html')

def show_asset_datatable(request):

    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        assets = ZetdcAssets.objects.all()
        print("assets ", assets)
    
        if search_value:
         assets = assets.filter(
            Q(asset_state__icontains=search_value) |
            Q(product_type__product_type__icontains=search_value) |
            Q(serial_number__icontains=search_value) |
            Q(sections__section__icontains=search_value) |
            Q(user__first_name__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(regions__region__icontains=search_value) |
            Q(purchase_cost__icontains=search_value) |
            Q(designations__description__icontains=search_value) |
            Q(model__icontains=search_value) |
            Q(warrant__icontains=search_value) |
            Q(created_by__icontains=search_value)
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
                "2": "product_type",
                "3": "serial_number",
                "4": "department",
                "5": "user",
                "6": "regions",
                "7": "purchase_cost",
                "8": "designations",
                "9": "date_purchased",
                "10": "warrant",
                "11": "model",
                "12": "created_by",
                "13": "created_at",

            }

            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}'  # Add descending order prefix
                assets= assets.order_by(column_name)


        # Pagination
        paginator = Paginator(assets, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)


        # print('my assets', asset.regions.region, asset.designations.description, )
        asset_list = []
        for asset in page_obj:
            print('my assets', asset.regions.region)
            new_asset = {
                "id": asset.id,
                "asset_state": asset.asset_state,
                "product_type": asset.product_type.product_type if asset.product_type else None,
                "serial_number": asset.serial_number,
                "department": asset.sections.section if asset.sections else None,
                "user": asset.user.first_name + " " + asset.user.last_name if asset.user else "",
                "regions": asset.regions.region if asset.regions else None,
                "purchase_cost": asset.purchase_cost,
                "designations": asset.designations.description if asset.designations else None,
                "date_purchased": asset.date_purchased,
                "warrant": asset.warrant,
                "model": asset.model,
                "created_by": asset.created_by,
                "created_at": asset.created_at,
            }
            asset_list.append(new_asset)
         
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
    
def update_asset(request, id):
  
  zetdcAssets = ZetdcAssets.objects.filter(id=id).first()
  
  print({
    'zetdcAssets': zetdcAssets,
    'id': zetdcAssets.id,
    'product_id': zetdcAssets.product_type,
})
 

  if request.method == 'POST':
        user_id = request.POST['user']
        user = User.objects.filter(id=user_id).first()

        region_id= request.POST['regions']
        regions = Regions.objects.filter(id=region_id).first()

        designation_id = request.POST['designations']
        designations = Designations.objects.filter(id=designation_id).first()
        
        section_id = request.POST['department']
        sections = Sections.objects.filter(id=section_id).first()
        print("request",request.POST)
        #form.save()
        
        
        zetdcAssets.product_id = request.POST['product_type']
        zetdcAssets.asset_state = request.POST['asset_state']
        zetdcAssets.serial_number = request.POST['serial_number']
        zetdcAssets.department = request.POST['department']
        zetdcAssets.user = user
        zetdcAssets.regions = regions
        zetdcAssets.purchase_cost = request.POST['purchase_cost']
        zetdcAssets.designations = designations
        zetdcAssets.sections = sections
        zetdcAssets.date_purchased = request.POST['date_purchased']
        zetdcAssets.warrant = request.POST['warrant']
        zetdcAssets.model = request.POST['model']
        #zetdcAssets.created_by = request.POST['created_by']
        zetdcAssets.save()
        return redirect('/table_asset')
        
  return render(request, 'asset_register/update_asset.html', {
        'zetdcAssets': zetdcAssets,
        'id': zetdcAssets.id,
        'product_id': zetdcAssets.product_type,
        'asset_state': zetdcAssets.asset_state,
        'serial_number': zetdcAssets.serial_number,
        'asset_number': zetdcAssets.id,  # If this refers to the asset number
        'department': zetdcAssets.department,
        'user': zetdcAssets.user,
        'regions': zetdcAssets.regions,
        'purchase_cost': zetdcAssets.purchase_cost,
        'designations': zetdcAssets.designations,
        'date_purchased': zetdcAssets.date_purchased,
        'warrant': zetdcAssets.warrant,
        'model': zetdcAssets.model,
        # Pass lists for dropdowns
        'product_types': ProductType.objects.all(),
        'sections': Sections.objects.all(),
        'users': User.objects.all(),
        'regions': Regions.objects.all(),
        'designations': Designations.objects.all(),
})


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
        print("product", product)

        if search_value:
            product = product.filter(
                product_type__icontains=search_value
            ) | product.filter(
                code__icontains=search_value
            )

        # Total number of records before filtering
        total = product.count()

          # Sorting
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column is not None and order_dir is not None:
            column_map = {
                "0": "id",
                "1": "product_type",
                "2": "code",
            }

            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}'  # Add descending order prefix
                product= product.order_by(column_name)


        # Pagination
        paginator = Paginator(product, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)


        product_list = []
        for product in page_obj:
            new_product = {
                "id": product.id,
                "product_type": product.product_type,
                "code": product.code,
            }
            product_list.append(new_product)
        print("product_list: ", product_list)
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
                "5": "purchase_cost",
                "6": "date_purchased",
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
                "department": asset.sections.section if asset.sections else None,
                "regions": asset.regions.region if asset.regions else None,
                "purchase_cost": asset.purchase_cost,
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
    if asset_state:
        assets = assets.filter(asset_state=asset_state)
    if sections:
        assets = assets.filter(sections=sections)
    if regions:
        assets = assets.filter(regions=regions)
    if pick_station:
        assets = assets.filter(pick_station=pick_station)
    if start_date:
        assets = assets.filter(date_purchased__gte=start_date)
    if end_date:
        assets = assets.filter(date_purchased__lte=end_date)

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Assets.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Product Type', 'Asset State', 'Department', 'Regions', 'Purchase Cost', 'Date Purchased'])

    for asset in assets:
        writer.writerow([asset.id, asset.product_type, asset.asset_state, asset.department, asset.regions, asset.purchase_cost, asset.date_purchased])

    return response

def upload_asset(request):
    if request.method == 'POST':

        csvfile = request.FILES['uploaded_csv'] # file as key
    
        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:        
            date = datetime.strptime(row['created_at'], "%Y-%m-%d")
            formatted_date = date.strftime("%Y-%m-%d")

            district = Sections.objects.filter(district=row['district']).first()
            section = Sections.objects.filter(section=row['section']).first()
            region = Regions.objects.filter(region=row['region']).first()
            designations = Designations.objects.filter(designations=row['designations']).first()

            new_zetdcassets = ZetdcAssets(

                product_type= row['product_type'], 
                asset_state= row['asset_state'],
                serial_number= row['serial_number'],
                asset_number= row['asset_number'],
                user= row['user'],
                date_purchased= row['date_purchased'],
                warrant = row['warant'],
                model = row['model'],
                purchase_cost= row['purchase_cost'],
                designations= designations,
                section=section,
                district=district,
                region=region,
                created_at=formatted_date,
                updated_at=formatted_date
            )
            new_zetdcassets.save()
        
        redirect('/table_asset')
            
    return render(request, 'asset_register/upload_asset.html', {})
