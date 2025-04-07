from django.urls import path
from .views import *

app_name = 'Ace'

urlpatterns = [
    path('create_ace', create_Ace, name='create_pettycash'),
    path('create_ace_report', ace_reports, name='create_ace_report'),
    path('print_report_csv/<str:report_id2>', ace_report_detail_excel, name='print_report_csv'),
    path('print_report_pdf/<str:report_id2>', ace_report_detail_pdf, name='print_report_pdf'),
    path('ace_detail/<str:Ace_id2>', Ace_detail, name='ace_detail'),
    path('ace_detail_project/<str:Ace_id2>', add_project_details, name='ace_detail_project'),
    path('aces', view_all_aces, name='view_all_aces'),
    path('upload_budget', upload_budgets, name='upload budget'),
    path('balance/<str:budget_id>', get_budget_balance, name='balance>'),
    path('attachment/<str:attachment_id>', download_attachment, name='attachment'),

    path('aces_awaiting_my_action', ace_awaiting_my_action, name='aces_awaiting_my_action'),
    path('budgets', list_budgets, name='view_all_budgets'),
    path('add_asset_number', add_asset_number, name='add_asset_number'),
    path('upload_ace', upload_aces_csv, name='upload_ace'),
    path('create_virament', create_virament, name='create_virament'),
    path('virament_detail/<str:virament_id>', virament_detail, name='virament_detail'),
    path('viraments', view_all_viraments, name='view_all_viraments'),
    path('viraments_awaiting_my_action', viraments_awaiting_my_action, name='viraments_awaiting_my_action'),
    path('transactions', view_all_transactions, name='view_all_transactions'),
    path('transactions_for_budget/<str:budget_id>', transactions_for_budget, name='transactions_for_budgets'),
    path('vir_and_ace/<str:budget_id>', transactions_view, name='vir_and_ace'),
    path('reports', reports_view, name='reports_view'),
    path('my_actioned/', my_actioned_items, name='my_actioned_items'),
]
