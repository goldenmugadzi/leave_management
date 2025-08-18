from django.urls import path

from . import views

urlpatterns = [
    path('controller/instructions/create', views.create_controller_instruction, name='create_controller_instruction'),
    path('controller/instructions/update', views.update_controller_instruction, name='update_controller_instruction'),
    path('controller/instructions/delete', views.delete_controller_instruction, name='delete_controller_instruction'),
    path('controller/instructions', views.get_controller_instructions, name='get_controller_instructions'),
    path('controller/instruction', views.get_controller_instruction, name='get_controller_instruction'),
    
    # generate urls for permit-to-work resource
    path('permit-to-work/create', views.create_permit_to_work, name='create_permit_to_work'),
    path('permit-to-work/update', views.update_permit_to_work, name='update_permit_to_work'),
    path('permit-to-work/delete', views.delete_permit_to_work, name='delete_permit_to_work'),
    path('permit-to-work/retrieve', views.get_permit_to_work, name='get_permit_to_work'),
    path('all-permit-to-work', views.get_all_permit_to_work, name='get_permit_to_works'),
    
    # urls for permit-to-work approvals
    path('permit-to-work/responsible-official/approve', views.responsible_official_approve, name="responsible_official_approve"),
    path('permit-to-work/receipt-person/approve', views.receipt_person_approve, name="receipt_person_approve"),
    path('permit-to-work/clearance-person/approve', views.clearance_person_approve, name="clearance_person_approve"),
    path('permit-to-work/senior-clearance/approve', views.snr_clearance_approve, name="snr_clearance_approve"),
    path('permit-to-work/official-clearance/approve', views.official_clearance_approve, name="official_clearance_approve"),
    path('permit-to-work/worker/approve', views.worker_approve, name="worker_approve"),

    # app users
    path('users', views.get_ops_users, name='ops_users')
    
]