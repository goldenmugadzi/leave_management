from django.urls import path
from .views import *
app_name = 'comparative_schedules'

urlpatterns = [
    path('schedule/<str:pr_id>', get_create_cs, name='adopt_schedule'),
    path('create_comperative_schedule/', create_comperative_schedule, name='create_comperative_schedule'),
    path('create_schedule/', create, name='create_schedule'),
    path('add_supplier/<str:tender_id>', cs_add_supplier, name='add_supplier'),
    path('compliance/<str:tender_id>', cs_compliance_table, name="tender_compliance"),

    path('create_data/<str:pr_id>', get_create_data, name='get_create_data'),
    path('save', save_comparative_schedule, name='save_schedule'),
    path('update', update_comparative_schedule, name='update_schedule'),
    
    path('save_supplier', save_supplier, name='save_supplier'),
    path('save_bid', save_cs_bid, name='save_bid'),
    path('delete_bid', delete_cs_bid, name='delete_cs_bid'),
    
    path('save_compliance', save_cs_compliance, name='save_compliance'),

    path('close_compliance', save_cs_ranking, name='save_cs_ranking'),
    path('save_committee', save_cs_committee, name='save_cs_committee'),
    path('delete_committee_member', delete_cs_committee_member, name='delete_cs_committee_member'),
    path('committee_approve', approve_cs_committee, name='approve_cs_committee'),
    path('save_decision', save_cs_decision, name='save_cs_decision'),
    
    path('approval_approve', approve_cs, name='approve_cs'),
    
    path('comperative_schedules', get_comperative_schedules, name='get_comperative_schedules'),
    path('comperative_schedule/<str:cs_id>', get_comperative_schedule, name='get_comperative_schedule'),
    path('cs_data/<str:cs_id>', get_comperative_schedule_data, name='get_comperative_schedule_data'),
    
    path('update_pritem_ordered', update_pritem_ordered, name='update_pritem_ordered'),
    path('import_old_rfq', import_old_rfq, name='import_old_rfq'),
    
    path('pending_commitee', get_pending_committee, name='get_pending_committee'),
    path('pending_gm_approval', get_pending_gm_approval, name='get_pending_gm_approval'),
    path('pending_fm_approval', get_pending_fm_approval, name='get_pending_fm_approval'),
    path('all_schedules', get_all_schedules, name='get_all_schedules'),
]
