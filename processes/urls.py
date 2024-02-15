from django.urls import path
from . import views

urlpatterns =[
#  path('view-process',views.view_process, name='view-process'),
  path('it-process/',views.view_it, name='it-process'),
  path('commercial-process/',views.view_commercial, name='commercial-process'),
  path('planning-processes/',views.view_planning, name='planning-processes'),
  path('maintenance-processes/',views.view_maintenance, name='maintenance-processes'),
  path('project-processes/',views.view_project, name='project-processes'),
  path('file_search/',views.file_search, name='file_search'),
  path('display/',views.view_img, name='display'),
  path('finance-processes/',views.view_finance, name='finance-processes'),
  path('HR-processes/',views.view_HR, name='HR-processes'),
  path('Engineeringlist-processes/',views.view_engineeringlist, name='Engineeringlist-processes'),
  path('procurement-processes/',views.view_procurement, name='procurement-processes'),
  path('revenue-processes/',views.view_revenue, name='revenue-processes'),
  path('client-processes/',views.view_client, name='client-processes'),
  path('payment-processes/',views.view_payment, name='payment-processes'),
  path('risk-processes/',views.view_risk, name='risk-processes'),
  path('management-processes/',views.view_management, name='management-processes'),

    path("forms_index",views.forms_index,name="Forms Index"),
    path("forms_upload",views.forms_upload,name="Forms Upload"),
    path("engineering_forms",views.engineering_forms,name="Engineering Forms"),
    path("finance_forms",views.finance_forms,name="Finance Forms"),
    path("hr_forms",views.hr_forms,name="Human Resources Forms"),
     path("it_forms",views.it_forms,name="IT Forms"),
    path("risk_forms",views.risk_forms,name="Risk Forms"),
    path("commercial_forms",views.commercial_forms,name="Commercial Forms"),
    path('file_searchx/',views.file_searchx, name='file_searchx'),
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
    
   
    
]