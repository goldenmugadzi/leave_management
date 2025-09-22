from django.urls import path
from .views import ControllersInstructionFormCreateView, ControllersInstructionFormListView

urlpatterns = [
    path('safety_table/', views.safety_table, name='safety_table'),
    path('reports/new/', views.safety_report_create, name='safety_report_create'),
    path('safety_report_data/', views.safety_report_data, name='safety_report_data'),
    path('safety_ytd/', views.safety_ytd, name='safety_ytd'),
    path('safety_update/<int:id>/', views.safety_update, name='safety_update'),
    path('accident/',views.create_accident, name='create_accident'),
    path('accident_datatable/',views.accident_reports_datatable, name='accident_reports_datatable'),
    path('table_accident/',views.table_accident, name='table_accident'),
    path('accident_report_dashboard/', views.accident_report_dashboard, name=' accident_report_dashboard')
]