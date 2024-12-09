from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect
from.forms import EmployeeForm
from .models import Employee
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from.models import Employee
import json
import csv
from django.http import HttpResponse
from datetime import date, datetime 
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q



def create_fault(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST or None)
        print("frm data: ", form.is_valid())
        print("request",request.POST )
        job_card_no = "JC"+ str(int(datetime.now().timestamp()))

        employee = Employee(
            jobcardnumber= job_card_no,
            eserialnumber= request.POST['eserialnumber'],
            eUsername= request.POST['eUsername'],
            ephoneextension= request.POST['ephoneextension'],
            efault= request.POST['efault'],
            erepairstatus= request.POST['erepairstatus'],
            elocation= request.POST['elocation'],
            eupdatedby= request.POST['eupdatedby'])
            
        print("empl data: ", employee)
        employee.save()
        print("Data saved successfully!")
        messages.success(request, "Fault created successfully!")
        
        return redirect('show_fault')
    return render(request, 'hardware_faults/create_fault.html',{})

def show_fault(request):

    return render(request, 'hardware_faults/table_fault.html')

def show_fault_datatable(request):

    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        employees = Employee.objects.all()

        if search_value:
         employees = employees.filter(
            Q(jobcardnumber__icontains=search_value) |
            Q(eserialnumber__icontains=search_value) |
            Q(eloggedindate__icontains=search_value) |
            Q(eUsername__icontains=search_value) |
            Q(ephoneextension__icontains=search_value) |
            Q(efault__icontains=search_value) |
            Q(erepairstatus__icontains=search_value) |
            Q(elocation__icontains=search_value) |
            Q(eupdatedby__icontains=search_value) |
            Q(elastupdate__icontains=search_value) 
           
        )

        # Total number of records before filtering
        total = employees.count()

         # Sorting
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column is not None and order_dir is not None:
            column_map = {
                "0": "jobcardnumber",
                "1": "eserialnumber",
                "2": "eloggedindate",
                "3": "eUsername",
                "4": "ephoneextension",
                "5": "efault",
                "6": "erepairstatus",
                "7": "elocation",
                "8": "eupdatedby",
                "9": "elastupdate",
            }

            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}'  # Add descending order prefix
                employees = employees.order_by(column_name)


        # Pagination
        paginator = Paginator(employees, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)

        # Prepare response
        data = []
        for employee in page_obj:
            o = {
                "jobcardnumber": employee.jobcardnumber,
                "serialnumber": employee.eserialnumber,
                "loggedindate": employee.eloggedindate,
                "username": employee.eUsername,
                "phoneextension": employee.ephoneextension,
                "fault": employee.efault,
                "repairstatus": employee.erepairstatus,
                "location": employee.elocation,
                "updatedby": employee.eupdatedby,
                "lastupdate": employee.elastupdate,
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

def update_fault(request, eserialnumber):
    employee = Employee.objects.filter(eserialnumber=eserialnumber).first()
    form = EmployeeForm(request.POST)
    if request.method == 'POST':
        print("request",request.POST)
        #form.save()
        
        employee.eUsername = request.POST['eUsername']
        employee.efault = request.POST['efault']
        employee.elocation = request.POST['elocation']
        employee.ephoneextension = request.POST['ephoneextension']
        employee.erepairstatus = request.POST['erepairstatus']
        employee.eupdatedby = request.POST['eupdatedby']
        employee.elastupdate = datetime.now()
        employee.save()
        return redirect('/table_fault')
        
    return render(request,'hardware_faults/update_fault.html',{'employee':employee})    

def delete(request, id):
    form = Employee.objects.filter(eserialnumber=id)
    form.delete()
    print ('golden')
    return redirect('/show')
    
def Tables (request):
  return render(request,'hardware_faults/table_fault.html')
  
  

