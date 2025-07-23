from django.urls import path
from .views import *
app_name = 'comparative_schedules'

urlpatterns = [
    path('timeline', debug_time, name='timeline'),
    path('schedule/<str:pr_id>', get_create_cs, name='adopt_schedule'),
    path('save_additional_notes', save_additional_notes, name='save_additional_notes'),
    path('save_buyers_notes', save_buyers_notes, name='save_buyers_notes'),
    path('cancel_schedule/<str:cs_id>', cancel_schedule, name='cancel_schedule'),
    path('create_comperative_schedule/', create_comperative_schedule, name='create_comperative_schedule'),
    # path('create_schedule/', create, name='create_schedule'),
    path('add_supplier/<str:tender_id>', cs_add_supplier, name='add_supplier'),
    path('compliance/<str:tender_id>', cs_compliance_table, name="tender_compliance"),

    path('create_data/<str:pr_id>/', get_create_data, name='get_create_data'),
    # New focused APIs
    path('api/pr-basic/<str:pr_id>/', api_get_pr_basic, name='api_get_pr_basic'),
    path('api/pr-items/<str:pr_id>/', api_get_pr_items, name='api_get_pr_items'),
    path('api/pr-attachments/<str:pr_id>/', api_get_pr_attachments, name='api_get_pr_attachments'),
    path('api/reference-data/', api_get_reference_data, name='api_get_reference_data'),
    
    # PR Items Management Tab (separate from main CS creation)
    path('api/cs-pr-items-management/<str:cs_id>/', api_get_cs_pr_items_management, name='api_get_cs_pr_items_management'),
    path('api/cs-pr-items-update/<str:cs_id>/', api_update_cs_pr_items, name='api_update_cs_pr_items'),
    
    # Individual API endpoints
    path('api/users/', api_get_users, name='api_get_users'),
    path('api/users-with-roles/', api_get_users_with_roles, name='api_get_users_with_roles'),
    path('api/suppliers/', api_get_suppliers, name='api_get_suppliers'),
    path('api/currencies/', api_get_currencies, name='api_get_currencies'),
    path('api/proc_plans/', api_get_proc_plans, name='api_get_proc_plans'),
    
    # Optimized CS data endpoints (lazy loading)
    path('api/cs-bids/<str:cs_id>/', api_get_cs_bids_optimized, name='api_get_cs_bids_optimized'),
    path('api/cs-compliance/<str:cs_id>/', api_get_cs_compliance_optimized, name='api_get_cs_compliance_optimized'),
    path('api/cs-committee/<str:cs_id>/', api_get_cs_committee_optimized, name='api_get_cs_committee_optimized'),
    path('api/cs-approvals/<str:cs_id>/', api_get_cs_approvals_optimized, name='api_get_cs_approvals_optimized'),
    path('api/cs-rankings/<str:cs_id>/', api_get_cs_rankings_optimized, name='api_get_cs_rankings_optimized'),
    
    path('save', save_comparative_schedule, name='save_schedule'),
    path('update', update_comparative_schedule, name='update_schedule'),
    path('update_pritem_ordered', update_pritem_ordered, name='update_pritem_ordered'),
    
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
    path('reports', reports_all_schedules, name='reports_all_schedules'),
    path('comperative_schedule/<str:cs_id>', get_comperative_schedule, name='get_comperative_schedule'),
    path('cs_data/<str:cs_id>/', get_comperative_schedule_data, name='get_comperative_schedule_data'),
    
    path('import_old_rfq', import_old_rfq, name='import_old_rfq'),
    path('add_cost_center', add_cost_center, name='add_cost_center'),
    
    path('pending_commitee', get_pending_committee, name='get_pending_committee'),
    path('your_schedules', your_comperative_schedules, name='your_comperative_schedules'),
    path('pending_gm_approval', get_pending_gm_approval, name='get_pending_gm_approval'),
    path('pending_fm_approval', get_pending_fm_approval, name='get_pending_fm_approval'),
    path('all_schedules', get_all_schedules, name='get_all_schedules'),
    path('datatables/export', get_csv_export, name='get_csv_export'),
    path('datatables/<str:view>', datatable_data, name='datatable_data'),
]