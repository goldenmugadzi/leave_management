from django.urls import path
from . import views

urlpatterns =[
#  path('view-process',views.view_process, name='view-process'),
  path('it-process/',views.view_it, name='it-process'),
  path('commercial-process/',views.view_commercial, name='commercial-process'),
  path('planning-processes/',views.view_planning, name='planning-processes'),
  path('maintenance-processes/',views.view_maintenance, name='maintenance-processes'),
  path('project-processes/',views.view_project, name='project-processes'),
  path('file_search/',views.file_search, name='file_search'),
  path('display/',views.view_img, name='display'),
  path('finance-processes/',views.view_finance, name='finance-processes'),
  path('HR-processes/',views.view_HR, name='HR-processes'),
  path('Engineeringlist-processes/',views.view_engineeringlist, name='Engineeringlist-processes'),
  path('procurement-processes/',views.view_procurement, name='procurement-processes'),
  path('revenue-processes/',views.view_revenue, name='revenue-processes'),
  path('client-processes/',views.view_client, name='client-processes'),
  path('payment-processes/',views.view_payment, name='payment-processes'),
  path('risk-processes/',views.view_risk, name='risk-processes'),



]