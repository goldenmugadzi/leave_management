from django.shortcuts import render
from django.views import View



def view_competence(request):
        return render(request, 'competence_building/competence.html')

def view_charts(request):
        return render(request, 'competence_building/charts.html')

def view_headoffice(request):
        return render(request, 'competence_building/headoffice.html')

def view_regionaloffice(request):
        return render(request, 'competence_building/regionaloffice.html')

def view_jobdescription(request):
        return render(request, 'competence_building/jobdescription.html')

def view_IT(request):
        return render(request, 'competence_building/IT.html')

def view_finance(request):
        return render(request, 'competence_building/finance.html')
   
def view_humanresource(request):
        return render(request, 'competence_building/humanresource.html')

def view_losscontrol(request):
        return render(request, 'competence_building/losscontrol.html')

def view_engineering(request):
        return render(request, 'competence_building/engineering.html')

def view_commercial(request):
        return render(request, 'competence_building/commercial.html')