from django.shortcuts import render, redirect
from .forms import AssetTransferForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import AssetTransfer

def create_asset_transfer(request):
    if request.method == "POST":
        form = AssetTransferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('table_transfer')
    else:
        form = AssetTransferForm()
    return render(request, 'asset_transfer/create_transfer.html', {'form': form})


def show_asset_transfer_datatable(request):
    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        asset_transfers = AssetTransfer.objects.all()

        # Filtering
        if search_value:
            asset_transfers = asset_transfers.filter(
                serial_number__icontains=search_value
            ) | asset_transfers.filter(
                asset_description__icontains=search_value
            ) | asset_transfers.filter(
                asset_number__icontains=search_value
            ) | asset_transfers.filter(
                transfer_from__icontains=search_value
            ) | asset_transfers.filter(
                transfer_to__icontains=search_value
            ) | asset_transfers.filter(
                reason_for_transfer__icontains=search_value
            )

        total = asset_transfers.count()

        # Sorting
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        column_map = {
            "0": "id",
            "1": "date",
            "2": "serial_number",
            "3": "asset_description",
            "4": "asset_number",
            "5": "transfer_from",
            "6": "transfer_to",
            "7": "reason_for_transfer",
            "8": "signature_sender",
            "9": "signature_recipient",
        }

        if order_column is not None and order_dir is not None:
            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}' 
                asset_transfers = asset_transfers.order_by(column_name)

        # Pagination
        paginator = Paginator(asset_transfers, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)

        data_list = []
        for asset in page_obj:
            data_list.append({
                "id": asset.id,
                "date": asset.date.strftime("%Y-%m-%d"),
                "serial_number": asset.serial_number,
                "asset_description": asset.asset_description,
                "asset_number": asset.asset_number,
                "transfer_from": asset.transfer_from,
                "transfer_to": asset.transfer_to,
                "reason_for_transfer": asset.reason_for_transfer,
                "signature_sender": asset.signature_sender,
                "signature_recipient": asset.signature_recipient,
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data_list
        })

    except Exception as ex:
        print(ex)
        return JsonResponse({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })
        
def table_transfer (request):
  return render(request,'asset_transfer/transfer_table.html')