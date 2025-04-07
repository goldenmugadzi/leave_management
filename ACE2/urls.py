from django.urls import path, include
from . import views

app_name = 'Ace'

urlpatterns = [
    path('ace_detail/<str:Ace_id2>/', views.Ace_detail, name='ace_detail'),
    path('create_ace/', views.create_Ace, name='create_ace'),
    path('aces_awaiting_my_action/', views.ace_awaiting_my_action, name='ace_awaiting_my_action'),
    path('aces/', views.view_all_aces, name='view_all_aces'),
    path('add_project_details/<str:Ace_id2>/', views.add_project_details, name='add_project_details'),
    path('upload_budgets/', views.upload_budgets, name='upload_budgets'),
    path('get_budget_balance/<int:budget_id>/', views.get_budget_balance, name='get_budget_balance'),
    path('attachment/<int:attachment_id>/', views.download_attachment, name='download_attachment'),
    path('budgets/', views.list_budgets, name='list_budgets'),
    path('add_asset_number/', views.add_asset_number, name='add_asset_number'),
    path('upload_aces_csv/', views.upload_aces_csv, name='upload_aces_csv'),
    path('create_virament/', views.create_virament, name='create_virament'),
    path('virament_detail/<str:virament_id>/', views.virament_detail, name='virament_detail'),
    path('viraments/', views.view_all_viraments, name='view_all_viraments'),
    path('viraments_awaiting_my_action/', views.viraments_awaiting_my_action, name='viraments_awaiting_my_action'),
    path('transactions/', views.view_all_transactions, name='view_all_transactions'),
    path('transactions/<int:budget_id>/', views.transactions_for_budget, name='transactions_for_budget'),
    path('reports/', views.ace_reports, name='ace_reports'),
    path('reports/<str:report_id2>/pdf/', views.ace_report_detail_pdf, name='ace_report_detail_pdf'),
    path('reports/<str:report_id2>/excel/', views.ace_report_detail_excel, name='ace_report_detail_excel'),
    path('my_actioned_items/', views.my_actioned_items, name='my_actioned_items'),
    
    # API endpoints
    path('api/', include('ACE2.api_urls')),
]
