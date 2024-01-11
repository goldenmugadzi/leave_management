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




   