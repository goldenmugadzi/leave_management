from django.urls import path
from . import views

urlpatterns = [
    path('create_transfer/', views.create_asset_transfer, name='create-asset-transfer'),
    path('transfer_datatable', views.show_asset_transfer_datatable, name='show_asset_transfer_datatable'),
    path('table_transfer/', views.table_transfer, name='table_transfer'),

]