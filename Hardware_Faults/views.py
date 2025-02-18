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
#from django.contrib.auth import get_user_model
from.models import*
from it.users.models import Regions, Sections, UserProfile
#User = get_user_model()

def create_fault(request):
    users = UserProfile.objects.all()
    regions = Regions.objects.all()
    sections = Sections.objects.all()
     
    if request.method == 'POST':
        # form = EmployeeForm(request.POST or None)
        # print("request.POST",)
        # if form.is_valid():
        region_id = request.POST.get('regions')
        section_id = request.POST.get('sections')
       # print("request.POST",sections)
        try:
            region = Regions.objects.get(id=region_id) if region_id else None
            section = Sections.objects.get(id=request.POST['department']) 

        except (Regions.DoesNotExist, Sections.DoesNotExist):
            #print("request.POST",regions)
            return redirect('create_fault')

        job_card_no = "JC" + str(int(datetime.now().timestamp()))
        user = UserProfile.objects.filter(id=request.POST['eUsername']).first()

        employee = Employee(
            jobcardnumber=job_card_no,
            eserialnumber=request.POST['eserialnumber'],
            eUsername=user.username,
            ephoneextension=request.POST['ephoneextension'],
            efault=request.POST['efault'],
            erepairstatus="logged in",
            department=request.POST['department'],
            regions=region,  
            sections=section, 
            eupdatedby=request.user,
            user=user
        )
        print("sections:", section_id)
        employee.save()
        messages.success(request, "Fault created successfully!")
        return redirect('show_fault')

    return render(request, 'hardware_faults/create_fault.html', {
        'users': users,
        'regions': regions,
        'sections': sections,
    })

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
            Q(department__icontains=search_value) |
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
                "7": "department",
                "8": "eupdatedby",
                "9": "elastupdate",
                "10": "regions",
                "11": "comment",
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
                "comment": employee.comment,
                "updatedby": employee.eupdatedby,
                 "department": employee.sections.section if employee.sections else None,
                 "regions":employee.regions.region if employee.regions else None,
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
    try:
        employee = Employee.objects.get(eserialnumber=eserialnumber) 
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('table_fault') 

    users = UserProfile.objects.all()
    regions = Regions.objects.all()
    sections = Sections.objects.all()

    if request.method == 'POST':
        region_id = request.POST.get('regions')
        section_id = request.POST.get('department')  # Change to 'department' instead of 'sections'
        user_id = request.POST.get('eUsername') 

        try:
            region = Regions.objects.get(id=region_id) if region_id else None
            section = Sections.objects.get(id=section_id) if section_id else None
            user = UserProfile.objects.get(id=user_id) if user_id else None 
        except (Regions.DoesNotExist, Sections.DoesNotExist, UserProfile.DoesNotExist):
            messages.error(request, "Invalid region, section, or user.")
            return redirect('update_fault', eserialnumber=eserialnumber)

        # Now that section is being retrieved by id, update department properly
        employee.userprofile = user 
        employee.efault = request.POST['efault']
        employee.department = section.id if section else employee.department  # Set department correctly
        employee.ephoneextension = request.POST['ephoneextension']
        employee.erepairstatus = request.POST['erepairstatus']
        employee.regions = region
        employee.sections = section
        employee.eupdatedby = request.user
        employee.comment = request.POST['comment']
        employee.elastupdate = datetime.now()

        # Save the employee, including department from form submission
        employee.save()

        messages.success(request, "Fault updated successfully!")
        return redirect('table_fault')

    initial_data = {
        'eserialnumber': employee.eserialnumber,
        'eUsername': employee.userprofile.id if employee.userprofile else None,
        'efault': employee.efault,
        'department': employee.department,  # Ensure this is populated with current department
        'ephoneextension': employee.ephoneextension,
        'erepairstatus': employee.erepairstatus,
        'regions': employee.regions.id if employee.regions else None, 
        'sections': employee.sections.id if employee.sections else None,
        'comment': employee.comment,
    }

    form = EmployeeForm(instance=employee, initial=initial_data)

    return render(request, 'hardware_faults/update_fault.html', {
        'employee': employee,
        'users': users,
        'regions': regions,
        'sections': sections,
        'form': form, 
    })

 

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

from datetime import datetime
from dateutil import parser

def upload_fault(request):
    if request.method == 'POST':
        print("POST Data:", request.POST)
        csvfile = request.FILES.get('uploaded_csv')
        
        if not csvfile:
            return render(request, 'asset_register/upload_asset.html', {'error': 'No file uploaded'})
        
        try:
            decoded_file = csvfile.read().decode('cp1252').splitlines()
            reader = csv.DictReader(decoded_file)
            reader.fieldnames = [header.strip() for header in reader.fieldnames]
            print("CSV Headers:", reader.fieldnames)

            for row in reader:
                date_string = row.get('date purchased') 
                parsed_date = None
                
                if date_string:
                    # Try parsing with the first format: '%A, %B %d, %Y'
                    try:
                        parsed_date = datetime.strptime(date_string, "%A, %B %d, %Y").date()
                    except ValueError:
                        print(f"Failed to parse with first format: {date_string}")
                    
                    if not parsed_date:
                        try:
                            parsed_date = datetime.strptime(date_string, "%d-%b-%y").date()
                        except ValueError:
                            print(f"Failed to parse with second format: {date_string}")
                    if not parsed_date:
                        print(f"Invalid date format for: {date_string}")

                # Check and print the parsed date for debugging
                print(f"Parsed Date: {parsed_date}")
                
                print("Processing row:", row)
                #product_type, _ = ProductType.objects.get_or_create(product_type=row.get('product type'))  
                section, _ = Sections.objects.get_or_create(section=row.get('department'))
                region, _ = Regions.objects.get_or_create(region=row.get("region"))
                print("region",region)

                loggedin_date = datetime.now().date()
                lastupdate = datetime.now().date()

                user = row.get('user').strip()
                print("region", region)

                new_employee = Employee(
                    serialnumber=serialnumber,
                    phoneextension=phoneextension,
                    fault=fault,
                    user_name=user,
                    repairstatus=repairstatus,
                    comment=comment,
                    sections=section,
                    regions=region,
                    loggedin_date=loggedin_date,
                    lastupdate=lastupdate,
                   
                )
                new_employee.save()

            return redirect('/table_fault/')
        except Exception as e:
            print("Error:", e)
            return render(request, 'hardware_faults/upload_fault.html', {'error': str(e)})

    return render(request, 'hardware_faults/upload_fault.html', {})
