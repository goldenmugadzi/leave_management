from django.urls import path
from .views import *

app_name = 'Ace'

urlpatterns = [
    path('create_ace', create_Ace, name='create_pettycash'),
    path('ace_detail/<str:Ace_id2>', Ace_detail, name='ace_detail'),
    path('ace_detail_project/<str:Ace_id2>', add_project_details, name='ace_detail_project'),
    path('aces', view_all_aces, name='view_all_aces'),
    path('upload_budget', upload_budgets, name='upload budget'),
    path('balance/<str:budget_id>', get_budget_balance, name='balance>'),
    path('attachment/<str:attachment_id>', download_attachment, name='attachment'),

    path('aces_awaiting_my_action', ace_awaiting_my_action, name='aces_awaiting_my_action'),
    path('budgets', list_budgets, name='view_all_budgets')
    # path('import_pettycash', import_pettycash, name='import_pettycash'),
    # path('receipt', receipt, name='receipt'),
]
