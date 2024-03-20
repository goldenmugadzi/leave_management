from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create', views.create_pettycash, name='create_pettycash'),
    path('list_requester', views.get_pettycash_records_requester, name='all_pettycash'),
    path('list_section_head', views.get_pettycash_records_section_head, name='section_head_pettycash'),
    path('list_pettycash_authoriser', views.get_pettycash_records_pettyauthoriser, name='pettycash_authoriser'),
    path('quotation_download', views.quotation_download, name='quotation_downloaded'),
    path('approve', views.get_to_approve_pettycash, name='approve_pettycash'),
    path('final_approve', views.final_approval, name='final_approval'),
    path('final_reject', views.final_reject, name='final_reject'),
    path('list_disburser', views.get_pettycash_records_disburser, name='all_pettycash'),
    path('disburse', views.disburse, name='disburse'),
    path('disburse_final', views.disburse_final, name='disburse_final'),
    path('reports', views.petty_reports, name='reports'),
    path('generate_report', views.generate_report, name='generate_report'),
]
