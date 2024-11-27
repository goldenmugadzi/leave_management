from django.contrib import admin
from django.urls import path,include
from .import views
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('create_fault/', views.create_fault, name="create_fault"),
    path('show_fault/', views.show_fault, name="show_fault"),
    path('update_fault/<str:eserialnumber>/', views.update_fault, name="update_fault"),
    path('delete/<int:id>', views.delete, name="delete"),
    path('home/', views.home, name="home"),
    path('table_fault/', views.show_fault, name="table_fault"),
    path('faults_datatable/', views.show_fault_datatable),
    path('Reports/', views.Reports, name="Reports"),
   
]   
