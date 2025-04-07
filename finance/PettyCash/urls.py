from django.urls import path
from .views import *

app_name = 'pettycash'

urlpatterns = [
    path('create_pettycash', create_pettycash, name='create_pettycash'),
    path('pettycash_detail/<str:petty_id>/', pettyCash_detail, name='pettycash_detail'),
    path('pettycashs', view_all_pettycashs, name='view_all_pettycashs'),
    path('pettycashs_awaiting_my_action', pettycash_awaiting_my_action, name='pettycashs_awaiting_my_action'),
    path('import_pettycash', import_pettycash, name='import_pettycash'),
    path('receipt', receipt, name='receipt'),
    path('attachment/<str:filename>/', download_file, name='attachment'),
    path('attachments/<str:attachment_id>', download_attachment, name='attachments'),
    path('create_pettycash_report', pettycash_report, name='pettycash_report'),
    path('print_report_csv/<str:report_id>', print_report_excel, name='print_report_csv'),
    path('receipt_manual', receipt_manual, name='receipt_manual'),
    path('my_actioned/', my_actioned_items, name='my_actioned_items'),
    # path('print_report_pdf', print_report_pdf, name='print_report_pdf'),
]
