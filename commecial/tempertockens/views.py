from django.shortcuts import render, redirect
from .models import MeterToken
from .forms import MeterTokenForm

def create_meter_token(request):
    if request.method == 'POST':
        form = MeterTokenForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('display_meter_tokens')
    else:
        form = MeterTokenForm()
    return render(request, 'commercials/tempertockens/create_meter_token.html', {'form': form})

def update_meter_token(request, pk):
    token = MeterToken.objects.get(pk=pk)
    if request.method == 'POST':
        form = MeterTokenForm(request.POST, instance=token)
        if form.is_valid():
            form.save()
            return redirect('display_meter_tokens')
    else:
        form = MeterTokenForm(instance=token)
    return render(request, 'commercials/tempertockens/update_meter_token.html', {'form': form})

def delete_meter_token(request, pk):
    token = MeterToken.objects.get(pk=pk)
    if request.method == 'POST':
        token.delete()
        return redirect('display_meter_tokens')
    return render(request, 'commercials/tempertockens/delete_meter_token.html', {'token': token})

def display_meter_tokens(request):
    tokens = MeterToken.objects.all()
    return render(request, 'commercials/tempertockens/display_meter_tokens.html', {'tokens': tokens})
