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
from exchangelib import Credentials, Account, Configuration, Message, Mailbox
from django.urls import reverse
from django.template.loader import render_to_string
from exchangelib import HTMLBody
from django.contrib.auth import get_user_model
from.models import*
User = get_user_model()

def create_fault(request):
    users = User.objects.all() 
    if request.method == 'POST':
        form = EmployeeForm(request.POST or None)
        print("frm data: ", form.is_valid())
        print("request",request.POST )
        job_card_no = "JC"+ str(int(datetime.now().timestamp()))
        user = User.objects.filter(id=request.POST['eUsername']).first()

        employee = Employee(
            jobcardnumber= job_card_no,
            eserialnumber= request.POST['eserialnumber'],
            eUsername= user.id,
            ephoneextension= request.POST['ephoneextension'],
            efault= request.POST['efault'],
            erepairstatus= request.POST['erepairstatus'],
            elocation= request.POST['elocation'],
            eupdatedby= request.user,
            user=user
            )
            
        print("empl data: ", employee)
        employee.save()
        print("Data saved successfully!")
        messages.success(request, "Fault created successfully!")
        print('user', users)
        return redirect('show_fault')
    return render(request, 'hardware_faults/create_fault.html',{'users': users})

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
            print(employee)
            o = {
                "jobcardnumber": employee.jobcardnumber,
                "serialnumber": employee.eserialnumber,
                "loggedindate": employee.eloggedindate,
                "username": employee.user,
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
    users = User.objects.all()
    form = EmployeeForm(request.POST)
    if request.method == 'POST':
        user_id = request.POST['eUsername']
        user = User.objects.filter(id=user_id).first()
        
        print("request",request.POST)
        #form.save()
        employee.eUsername = user_id
        employee.efault = request.POST['efault']
        employee.elocation = request.POST['elocation']
        employee.ephoneextension = request.POST['ephoneextension']
        employee.erepairstatus = request.POST['erepairstatus']
        employee.eupdatedby = request.POST['eupdatedby']
        employee.elastupdate = datetime.now()
        employee.save()
       
        notify_fault_update(request,employee)

        return redirect('/table_fault')
        
    return render(request,'hardware_faults/update_fault.html',{'employee':employee, 'users':users})   

def notify_fault_update(request, employee):
   
    user = User.objects.get(id=employee.eUsername)
    subject = f"Hardware Fault Update: {user.first_name} {user.last_name}"

    # Email recipients (can be dynamic based on your logic)
    recipients = [
        {"email": user.email},
       
    ]
    # Construct email context for the template
    context = {
    "user_fullname": f"{user.first_name} {user.last_name}",
    "message": f"The fault update for {employee.efault} is {employee.erepairstatus} for more information contact the Hardware Technician {employee.eupdatedby} at the workshop with the following reference {employee.jobcardnumber}",
    "fault_details": {
        "Username": employee.eUsername,
        "Fault": employee.efault,
        "Repair Status": employee.erepairstatus,
    },
}

    # Render the email body from the template
    email_body = render_to_string('email/email_template.html', context)

    # Send the email to each recipient
    for recipient in recipients:
        try:
            response = ms_exhange_send(
                subject=subject,
                body=email_body, 
                to_recipients=[recipient["email"]],
                cc_recipients=[],
            )
            if response.status_code != 200:
                messages.error(request, f"Failed to notify {recipient['name']} ({recipient['email']}).")
        except Exception as e:
            messages.error(request, f"Error sending email to {recipient['email']}: {e}") 

def delete(request, id):
    form = Employee.objects.filter(eserialnumber=id)
    form.delete()
    print ('golden')
    return redirect('/show')
    
def Tables (request):
  return render(request,'hardware_faults/table_fault.html')
  
 
def get_exchange_account():

    from decouple import config as cnf
    print(cnf)
    credentials = Credentials(
        username='bexcel@zedc.co.zw',
        password='Zesazesa_2024'
    )
    print("Credentials: ", credentials)
    config = Configuration(
        server='mail.zesaholdings.co.zw',
        credentials=credentials,
    )
    print("Config: ", config)
    account = Account(
        primary_smtp_address='bexcel@zedc.co.zw',
        config=config,
        autodiscover=False,
        access_type='delegate'
    )
    print("Successfully connected to Exchange server.")
    return account

@login_required
def ms_exhange_test(request):
    account = get_exchange_account()
    message = Message(
        account=account,
        folder=account.sent,
        subject="Test Email",
        body="This is a test email",
        to_recipients=[Mailbox(email_address='goldenmugadzi@gmail.com')]
    )
    message.send()
    return JsonResponse({"status": "success", "message": "Email sent successfully"})

def ms_exhange_send(subject, body, to_recipients, cc_recipients):
    account = get_exchange_account()
    message = Message(
        account=account,
        folder=account.sent,
        subject=subject,
        body=HTMLBody(body), 
        to_recipients=[Mailbox(email_address=recipient) for recipient in to_recipients],
        cc_recipients=[Mailbox(email_address=recipient) for recipient in cc_recipients]
    )
    message.send()
    return JsonResponse({"status": "success", "message": "Email sent successfully"})

