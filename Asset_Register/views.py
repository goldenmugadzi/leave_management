from django.shortcuts import render, redirect
from datetime import datetime
from django.core.paginator import Paginator
from django.http import JsonResponse
import json, os
from django.conf import settings
from django.contrib.auth import get_user_model

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

def show_asset_datatable(request):

    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        assets = ZetdcAssets.objects.all()
        print("assets ", assets)

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
    
def update_asset(request, asset_id):
    url_path = request.path.split("/")
    if request.method == 'GET':
        print("asset_id: ", asset_id)
        asset_record = ZetdcAssets.objects.filter(id=asset_id).first()
        # fetch section code

        url_path = request.path.split("/")
        return render(request, 'home/edit.html', {"record": asset_record, "url_path": url_path})    
    
    if request.method == 'POST':
        # something
        print("post data: ", request.POST)
        id = request.POST['id']
        asset_state = request.POST['asset_state']
        product_id = request.POST['product_id']
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

        # asset_state= ZetdcAssets.objects.filter(id=id).first() if id else None
        
        um = ZetdcAssets.objects.filter(id=id).first()
        um.asset_state= asset_state
        um.product_type= product_id if product_id else ""
        um.serial_number = serial_number
        um.asset_number= asset_number
        um.department = department if department else ""
        um.user=user
        um.regions=regions if regions else ""
        um.purchase_cost=purchase_cost
        um.designations=designations if designations else ""
        um.date_purchased=date_purchased
        um.warrant=warrant
        um.model=model
        um.updated_at = datetime.now().date()
        um.created_by = "Goldy"

        um.save()
        # fetch section code

        url_path = request.path.split("/")
        return render(request, 'home/edit.html', {"record": um, "url_path": url_path})    
      
    
    return render(request, 'home/edit.html', {"url_path": url_path})
