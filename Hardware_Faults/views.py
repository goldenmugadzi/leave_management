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
from.models import*
from it.users.models import Regions, Sections, UserProfile

def createFault(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  
            return redirect('show_fault') 
        else:
        
            print(form.errors)  
    else:
        form = EmployeeForm()

    return render(request, "hardware_faults/createFault.html", {"form": form})

def show_fault(request):

    return render(request, 'hardware_faults/table_fault.html')

def show_fault_datatable(request):
    try:
        draw = int(request.GET.get('draw', default=1))
        start = int(request.GET.get('start', default=0))
        length = int(request.GET.get('length', default=10))
        search_value = request.GET.get('search[value]', default='')

        user_region = None
        if hasattr(request.user, 'region') and request.user.region:
            user_region = request.user.region

        employees = Employee.objects.all()

        if user_region:
            employees = employees.filter(regions=user_region)

        if search_value:
            employees = employees.filter(
                Q(jobcardnumber__icontains=search_value) |
                Q(serialnumber__icontains=search_value) |
                Q(loggedindate__icontains=search_value) |
                Q(user__username__icontains=search_value) | 
                Q(phoneextension__icontains=search_value) |
                Q(fault__icontains=search_value) |
                Q(repairstatus__icontains=search_value) |
                Q(department__icontains=search_value) |
                Q(updatedby__icontains=search_value) |
                Q(lastupdate__icontains=search_value)
            )

        # Total number of records before filtering
        total = employees.count()

        # Sorting
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column is not None and order_dir is not None:
            column_map = {
                "0": "jobcardnumber",
                "1": "serialnumber",
                "2": "loggedindate",
                "3": "user", 
                "4": "phoneextension",
                "5": "fault",
                "6": "repairstatus",
                "7": "department",
                "8": "updatedby",
                "9": "lastupdate",
                "10": "regions",
                "11": "comment",
            }

            column_name = column_map.get(order_column)
            if column_name:
                if order_dir == 'desc':
                    column_name = f'-{column_name}' 
                employees = employees.order_by(column_name)

        # Pagination
        paginator = Paginator(employees, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)

        # Prepare response
        data = []
        for employee in page_obj:
            #print(f"Employee ID: {employee.id}, Cost Center: {employee.cost_center.name if employee.cost_center else 'None'}")
            o = {
                "jobcardnumber": employee.jobcardnumber,
                "serialnumber": employee.serialnumber,
                "loggedindate": employee.loggedindate,
                "user": f"{employee.user.first_name} {employee.user.last_name}" if employee.user else None,
                "phoneextension": employee.phoneextension,
                "fault": employee.fault,
                "repairstatus": employee.repairstatus,
                "comment": employee.comment,
                "updatedby":f"{employee.user.first_name} {employee.user.last_name}" if employee.user else None,
                "department": employee.department.section if employee.department else None,
                "regions": employee.regions.region if employee.regions else None,
                "lastupdate": employee.lastupdate,
                "cost_center": employee.cost_center.name if employee.cost_center else None,
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

def update_fault(request, serialnumber):
    print("message",serialnumber)
    try:
        employee = Employee.objects.get(serialnumber=serialnumber)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('table_fault') 
    except Employee.MultipleObjectsReturned:
        messages.error(request, "Multiple employees found with the same serial number.")
        return redirect('table_fault')

    users = UserProfile.objects.all()
    regions = Regions.objects.all()

    if request.method == 'POST':
        region_id = request.POST.get('regions')
        
        try:
            region = Regions.objects.get(id=region_id) if region_id else None
        except Regions.DoesNotExist:
            messages.error(request, "Invalid region.")
            return redirect('update_fault', serialnumber=serialnumber)

        # Save original values for comparison
        original_status = employee.repairstatus
        original_comment = employee.comment

        # Update employee fields
        employee.fault = request.POST.get('fault', employee.fault)
        employee.phoneextension = request.POST.get('phoneextension', employee.phoneextension)
        employee.repairstatus = request.POST.get('repairstatus', employee.repairstatus)
        employee.regions = region 
        employee.comment = request.POST.get('comment', employee.comment)
        employee.lastupdate = datetime.now()

        try:
            employee.save()
            messages.success(request, "Fault updated successfully!")
            
            # Only send email if repair status or comment changed
            if (original_status != employee.repairstatus) or (original_comment != employee.comment):
                print("message",Message)
                try:
                    notify_fault_update(request, employee)
                    messages.info(request, "Notification email sent to user.")
                except Exception as e:
                    messages.warning(request, f"Fault updated but email notification failed: {str(e)}")
            
            return redirect('table_fault')
        except Exception as e:
            messages.error(request, f"Error saving changes: {str(e)}")
            return redirect('update_fault', serialnumber=serialnumber)

    initial_data = {
        'serialnumber': employee.serialnumber,
        'user': employee.user.id if employee.user else None,
        'fault': employee.fault,
        'phoneextension': employee.phoneextension,
        'repairstatus': employee.repairstatus,
        'regions': employee.regions.id if employee.regions else None,
        'comment': employee.comment,
    }

    form = EmployeeForm(instance=employee, initial=initial_data)

    return render(request, 'hardware_faults/update_fault.html', {
        'employee': employee,
        'users': users,
        'regions': regions,
        'form': form, 
    })


def notify_fault_update(request, employee):
    print("employee",employee)
    try:
        user = employee.user
        if not user:
            raise ValueError("No user associated with this employee")
            
        subject = f"Hardware Fault Update: {employee.serialnumber}"

        context = {
            "user_fullname": f"{user.first_name} {user.last_name}",
            "message": f"The status of your hardware fault has been updated.",
            "fault_details": {
                "Asset Serial": employee.serialnumber,
                "Fault Description": employee.fault,
                "Repair Status": employee.repairstatus,
                "Comments": employee.comment,
                "Last Updated": employee.lastupdate.strftime("%Y-%m-%d %H:%M"),
            },
        }

        email_body = render_to_string('email/email_template.html', context)
        print("email_body",email_body),
        response = ms_exhange_send(
            subject=subject,
            body=email_body, 
            to_recipients=[user.email],
            cc_recipients=[],  
        )
        print("response",response)
        if response.status_code != 200:
            raise Exception(f"Email server returned status {response.status_code}")

    except Exception as e:
        print(f"Error sending notification email: {str(e)}")
        
        raise

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
    print("account",account),

    message = Message(
        account=account,
        folder=account.sent,
        subject=subject,
        body=HTMLBody(body), 
        to_recipients=[Mailbox(email_address=recipient) for recipient in to_recipients],
        cc_recipients=[Mailbox(email_address=recipient) for recipient in cc_recipients]
    )
    print("message",message),
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
                    serialnumber= row.get('serialnumber'),
                    phoneextension=row.get('phoneextension'),
                    fault=row.get('fault'),
                    user_name=user,
                    repairstatus=row.get('repairstatus'),
                    comment=row.get('comment'),
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
