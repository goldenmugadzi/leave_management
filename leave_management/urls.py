from django.urls import path
from . import views
from leave_management.views import encashment_leave

urlpatterns = [

    path('leave/', views.leave_create, name='leave_create'),
    path('leave_request_datatable/', views.leave_request_datatable, name='leave_request_datatable'),
    path('leave_table/', views.table_leave, name='table_leave'),
    path('create_leave_types/', views.create_leave_types, name='create_leave_types'),
    path('leave_types_datatable/', views.leave_types_datatable, name='leave_types_datatable'),
    path('leave_types/', views.leave_types, name='leave_types'),
    path('accumulate_vacation/<int:pk>/<str:employee_type>/', views.accumulate_vacation_leave_view, name='accumulate_vacation_leave'),
    path('approve_leave/<int:pk>/', views.approve_leave, name='approve_leave'),
    path('encashment/', encashment_leave, name='encashment'),
    path('update_leave/<int:id>/', views.update_leave_request, name='update_leave_request'),

]