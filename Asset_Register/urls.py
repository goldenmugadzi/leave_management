from django.urls import path

from . import views

urlpatterns = [
    path('create_asset', views.create_asset, name='create_asset'),
    path('show_asset/', views.show_asset, name="show_asset"),
    path('update_asset/<str:id>/', views.update_asset, name="update_asset"),
    path('table_asset/', views.show_asset, name="table_asset"),
    path('asset_datatable/', views.show_asset_datatable),
]