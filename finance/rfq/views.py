from django.shortcuts import render

from it.users.models import *

# Create your views here.
def index(request):
    return render(request, 'rfq/index.html')
