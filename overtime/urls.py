from django.urls import path
from . import views

app_name = "overtime"

urlpatterns = [
	path("create/", views.create_overtime_entry, name="create_entry"),
	path("table/",views.overtime_list, name="list"),
    path('overtime_datatable/', views.overtime_datatable, name='overtime_datatable'),
]