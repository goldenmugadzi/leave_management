from django.urls import path

from . import views

urlpatterns = [
    path('competence', views.view_competence, name='competence'),
    path('charts', views.view_charts, name='charts'),
    path('headoffice', views.view_headoffice, name='headoffice'),
    path('regionaloffice', views.view_regionaloffice, name='regionaloffice'),
    path('jobdescription', views.view_jobdescription, name='jobdescription'),



]