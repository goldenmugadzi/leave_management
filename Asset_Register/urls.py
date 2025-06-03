from django.urls import path

from . import views

urlpatterns = [
    #urls for assets
    path('create_asset', views.create_asset, name='create_asset'),
    path('show_asset/', views.show_asset, name="show_asset"),
    path('asset_report/', views.show_report, name="show[_report"),
    path('update_asset/<str:asset_type>/<int:asset_id>/', views.update_asset, name='update_asset'),
    path('show_combined_assets/', views.show_combined_assets, name= "show_combined_assets"),
    path('table_asset/', views.show_asset, name="table_asset"),
    path('tab/', views.tab,name="tab"),
    path('asset_datatable/', views.show_asset_datatable),
    path('report_datatable/', views.show_report_datatable),
    path('export_csv/', views.export_csv, name='export_csv'),
    path('upload_asset/', views.upload_asset, name='upload_asset'),

    #urls for product assets
    path('create_product', views.create_product, name='create_product'),
    path('table_product/', views.show_product, name="table_product"),
    path('product_datatable/', views.show_product_datatable),
    path('update_product/<str:id>/', views.update_product, name="update_product"),
   
    #urls for furniture
    path('table_hr', views.show_table, name='table_hr'),
    # path('create_hr', views.create_hr, name='create_hr'),
    path('hr_datatable/', views.show_hr_datatable),
    path('combined_assets_datatable', views.combined_assets_datatable, name='combined_assets_datatable'),

    #url for asset state chart data
    path('asset_state_chart_data/', views.asset_state_chart_data, name='asset_state_chart_data'),

]

