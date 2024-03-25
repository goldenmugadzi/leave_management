from django.urls import path
from . import views

urlpatterns =[
#  path('view-process',views.view_process, name='view-process'),

    path('process_maps/',views.view_Map, name='process_maps'),
    path('',views.index,name='index'),
    path('create/',views.create,name='create process map'),
    path('table/',views.view_process_map_table,name='process map table'),
    path('client/',views.view_Client,name='commercial client processes'),
    path('payment/',views.view_payment,name='commercial payment processes'),
    path('revenue/',views.view_revenue_assurance,name='revenue'),
    path('planning/',views.view_eng_planning,name='planning'),
    path('maintenance/',views.view_Maintenance,name='maintenance'),
    path('project/',views.view_eng_project,name='engineering project processes'),
    path('download_file/', views.download_file, name='download_file'),
    path('procurement/',views.view_Procurement,name='procurement'),
    path('finance/',views.view_Finance,name='finance'),
    path('ict/',views.view_ICT,name='ict'),
    path('hr/',views.view_HR,name='hr'),
    path('risk/',views.view_Risk,name='risk'),
    path('testadd/',views.bulk_create,name='bulk_create'),
    path('commercial/',views.view_Commercial,name='Commercial Processes'),
    path('engineering/',views.view_Engineering,name='Engineering Processes'),
    # path('edit_file',views.edit_file,name='edit'),
    
    path("forms_index",views.forms_index,name="Forms Index"),
    path("engineering_forms",views.engineering_forms,name="Engineering Forms"),
    path("finance_forms",views.finance_forms,name="Finance Forms"),
    path("hr_forms",views.hr_forms,name="Human Resources Forms"),
     path("it_forms",views.it_forms,name="IT Forms"),
    path("risk_forms",views.risk_forms,name="Risk Forms"),
    path("commercial_forms",views.commercial_forms,name="Commercial Forms"),
    path("new_view",views.new_view,name="Processes and Procedures"),
   
    path('viewWorkInstr',views.viewWorkInstr, name='viewWorkInstr'),
    path('viewEngProcedureHome',views.viewEngProcedureHome, name='Eng_ProcedureHome'),
    path('viewCommercialProcedureHome',views.viewCommercialProcedureHome, name='Commercial_ProcedureHome'),
    path('viewFinanceProcedures',views.viewFinanceProcedures, name='FinanceProcedures'),
    path('viewHRProcedures',views.viewHRProcedures, name='HR_Procedures'),
    path('viewSRProcedures',views.viewSRProcedures, name='Stakeholder Relations'),
    path('viewLegalProcedures',views.viewLegalProcedures, name='Legal Procedures'),
    path('viewProcurementProcedures',views.viewProcurementProcedures, name='Procurement Procedures'),
     path('viewICTProcedures',views.viewICTProcedures, name='ICT Procedures'),
    path('viewICT_WorkInstr',views.viewICT_WorkInstr, name='ICT Procedures and WorkInstr'),
    path('viewEng_PlanningProcedure',views.viewEng_PlanningProcedure, name='Eng_PlanningProcedure'),
    path(' viewEng_MaintananceProcedure',views. viewEng_MaintananceProcedure, name='Eng_MaintananceProcedure'),
    path(' viewEng_ProjectsProcedure',views. viewEng_ProjectsProcedure, name='Engineering Projects Planning'),
    path(' viewRiskProcedures',views. viewRiskProcedures, name='RiskProcedures'),
    path(' viewClientInteractionProcedures',views. viewClientInteractionProcedures, name='Client Procedures'),
    path(' viewPaymentProcedures',views. viewPaymentProcedures, name='Payment Procedures'),
    path(' viewRevenueAssuranceProcedures',views. viewRevenueAssuranceProcedures, name='Revenue Procedures'),
    path(' create',views.create, name='Upload Procedures and Work Instr')
   
    
]
