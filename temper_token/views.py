from django.shortcuts import render, redirect
from .forms import  MeterForm, CustomerForm,ReasonForm
from .models import *

def create_tempertoken(request):
    if request.method == 'POST':
        meter_form = MeterForm(request.POST)
        customer_form = CustomerForm(request.POST)
        if meter_form.is_valid() and customer_form.is_valid():
            meter = meter_form.save()
            customer = customer_form.save()
            temper_token = TemperToken.objects.create(**{'meter': meter,'customer': customer,'created_by': request.user,})
            if request.POST['reason']=='fault': Fault.objects.create(**{'temper_token': temper_token,'description': request.POST['description'],})
            elif request.POST['reason']=='recover': Recover.objects.create(**{'temper_token': temper_token,'description': request.POST['description'],})
            elif request.POST['reason']=='reconnection': Reconnection.objects.create(**{'temper_token': temper_token,'description': request.POST['description'],})
            # else: add a validation error
            return redirect('/')
        else: return render(request, 'temper_token/create_tempertoken.html', {'Customer': customer_form ,'Meter': meter_form })

    return render(request, 'temper_token/create_tempertoken.html', {'Customer': CustomerForm, 'reason':ReasonForm ,'Meter': MeterForm })

def view_all_tempertokens(request):return render(request, 'temper_token/tempertokens.html', {'tempertokens': TemperToken.objects.all()})    