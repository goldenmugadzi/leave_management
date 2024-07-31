from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import *

urlpatterns = [
    path('competence', view_competence, name='competence'),
    path('charts', view_charts, name='charts'),
    path('qualifications', view_qualifications, name='qualifications'),
    path('qualifications/<str:folder_name>', view_qualifications_files, name='view_qualifications_files'),
    path('headoffice', view_headoffice, name='headoffice'),
    path('regionaloffice', view_regionaloffice, name='regionaloffice'),
    path('jobdescription', view_jobdescription, name='jobdescription'),
    path('IT', view_IT, name='IT'),
    path('finance', view_finance, name='finance'),
    path('humanresource', view_humanresource, name='humanresource'),
    path('losscontrol', view_losscontrol, name='losscontrol'),
    path('engineering', view_engineering, name='engineering'),
    path('commercial', view_commercial, name='commercial'),
    path('district', view_district, name='district'),
    path('eastsales', view_eastsales, name='eastsales'),
    path('networkdevelopment', view_networkdevelopment, name='networkdevelopment'),
    path('operations', view_operations, name='operations'),
    path('suplies', view_suplies, name='suplies'),
    path('southdistrict', view_southdistrict, name='southdistrict'),
    
    
    path('southengineering', view_southengineering, name='southengineering'), 
    path('southglenview', view_southglenview, name='southglenview'),
    path('southwaterfalls', view_southwaterfalls, name='southwaterfalls'),
    path('southsales', view_southsales, name='southsales'),
    path('procurement', view_procurement, name='procurement'),
    path('northdistrict', view_northdistrict, name='northdistrict'),
    path('northkuwadzana', view_northkuwadzana, name='northkuwadzana'),
    path('northmabelreign', view_northmabelreign, name='northmabelreign'),
    path('northwarrenpark', view_northwarrenpark, name='northwarrenpark'),
    path('northsales', view_northsales, name='northsales'),
    path('eastdistrict', view_eastdistrict, name='eastdistrict'),
    path('eastcbd', view_eastcbd, name='eastcbd'),
    path('eastruwa', view_eastruwa, name='eastruwa'),
    path('eastborrowdale', view_eastborrowdale, name='eastborrowdale'),
    path('eastmabvuku', view_eastmabvuku, name='eastmabvuku'),
    path('chitownsales', view_chitownsales, name='chitownsales'),
    path('chitownzengeza', view_chitownzengeza, name='chitownzengeza'),
    path('chitownseke', view_chitownseke, name='chitownseke'),
    path('chitowndistrict', view_chitowndistrict, name='chitowndistrict'),
    path('itjobdescription', view_itjobdescription, name='itjobdescription'),
    path('procjobdescription', view_procjobdescription, name='procjobdescription'),
    path('srjobdescription', view_srjobdescription, name='srjobdescription'),
    path('riskjobdescription', view_riskjobdescription, name='riskjobdescription'),
    path('legaljobdescription', view_legaljobdescription, name='legaljobdescription'),
    path('hrjobdescription', view_hrjobdescription, name='hrjobdescription'),
    path('finjobdescription', view_finjobdescription, name='finjobdescription'),
    path('engjobdescription', view_engjobdescription, name='engjobdescription'),
    path('comjobdescription', view_comjobdescription, name='comjobdescription'),
    path('eastengineering', view_eastengineering, name='eastengineering'),
    path('easternregion', view_easternregion, name='easternregion'),
    path('chitownengineering', view_chitownengineering, name='chitownengineering'),
    path('northengineering', view_northengineering, name='northengineering'),
    path('southertoncommercial', view_southertoncommercial, name='southertoncommercial'),
    path('rfqview',view_rfqview, name='rfqview'),
    path('upload_file',view_upload_file, name='upload_file'),
    path('categories',view_categories, name='categories'),
    path('<int:category>/files',view_files, name='files'),
    path('competence_index', uploaded_jobs_view, name='competence_index'),
    path('bulk', bulk_create, name='bulk_create'),
    path('download', download_file, name='download_file'),
    path('edit_document/<int:document_id>', edit_document, name='edit_document'),
    path('archive_document/', view_archived_documents, name='archive_document'),
    path('archive', archived_documents, name='archive'),
    path('archive_file/<str:file_id>', archive_file, name='archive_file'),
    path('unarchive_file/<str:file_id>', unarchive_file, name='unarchive_file'),
    path('create_subcategory/', create_subcategory, name='create_subcategory'),
    path('subcategories/', Subcategory, name='subcategory'),
    path('vacancies', vacancies_view, name='vacancies'),
    path('safety', safetycircula_view, name ='safety'),
    path('upcoming_events', upcomingEvents_view, name ='upcoming_events'),
    path('trainings', trainingDevelopment_view, name ='trainigs'),

    


    






]
