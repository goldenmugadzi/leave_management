from django.urls import path

from . import views

urlpatterns = [
    path('create_asset', views.create_asset, name='create_asset'),
    path('show_asset/', views.show_asset, name="show_asset"),
    path('update_asset/<str:id>/', views.update_asset, name="update_asset"),
    path('update_product/<str:id>/', views.update_product, name="update_product"),
    path('table_asset/', views.show_asset, name="table_asset"),
    path('asset_datatable/', views.show_asset_datatable),
    path('create_product', views.create_product, name='create_product'),
    path('table_product/', views.show_product, name="table_product"),
    path('product_datatable/', views.show_product_datatable),
    path('show_asset_report/', views.show_asset_report, name="show_asset_report"),
    path('show_report_datatable/', views.show_report_datatable)

]