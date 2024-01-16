from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create', views.create_Ace, name='create_Ace'),
    path('list_requester', views.get_Ace_records_requester, name='all_Ace'),

    path('list_Ace_authoriser', views.get_Ace_records_pettyauthoriser, name='Ace_authoriser'),
    path('quotation_download', views.quotation_download, name='quotation_downloaded'),
    path('approve', views.get_to_approve_Ace, name='approve_Ace'),
    path('reject', views.get_to_reject_Ace, name='reject_Ace'),
    path('final_approve', views.final_approval, name='final_approval'),
    path('final_reject', views.final_reject, name='final_reject'),

    path('disburse', views.disburse, name='disburse'),
    path('disburse_final', views.disburse_final, name='disburse_final'),
    path('reports', views.petty_reports, name='reports'),
    path('generate_report', views.generate_report, name='generate_report'),
    path('create_budget', views.create_budget, name='create budget'),
    path('budgets', views.list_budgets, name='list budgets'),

    path('list_accounting_officer', views.get_Ace_records_accounting_officer, name='all_Ace'),
    path('list_section_head', views.get_Ace_records_section_head, name='section_head_Ace'),
    path('list_fm', views.get_Ace_records_fm, name='fm ace records'),
    path('list_gm', views.get_Ace_records_gm, name='gm ace records'),
]
