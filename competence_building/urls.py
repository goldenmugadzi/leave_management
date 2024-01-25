from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('competence', views.view_competence, name='competence'),
    path('charts', views.view_charts, name='charts'),
    path('headoffice', views.view_headoffice, name='headoffice'),
    path('regionaloffice', views.view_regionaloffice, name='regionaloffice'),
    path('jobdescription', views.view_jobdescription, name='jobdescription'),
    path('IT', views.view_IT, name='IT'),
    path('finance', views.view_finance, name='finance'),
    path('humanresource', views.view_humanresource, name='humanresource'),
    path('losscontrol', views.view_losscontrol, name='losscontrol'),
    path('engineering', views.view_engineering, name='engineering'),
    path('commercial', views.view_commercial, name='commercial'),


]
