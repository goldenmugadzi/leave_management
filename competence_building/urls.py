from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('competence', views.view_competence, name='competence'),
    path('charts', views.view_charts, name='charts'),
    path('headoffice', views.view_headoffice, name='headoffice'),
    path('regionaloffice', views.view_regionaloffice, name='regionaloffice'),
    path('jobdescription', views.view_jobdescription, name='jobdescription'),
    path('IT', views.view_IT, name='IT'),
    path('finance', views.view_finance, name='finance'),
    path('humanresource', views.view_humanresource, name='humanresource'),
    path('losscontrol', views.view_losscontrol, name='losscontrol'),
    path('engineering', views.view_engineering, name='engineering'),
    path('commercial', views.view_commercial, name='commercial'),
    path('district', views.view_district, name='district'),
    path('eastsales', views.view_eastsales, name='eastsales'),
    path('networkdevelopment', views.view_networkdevelopment, name='networkdevelopment'),
    path('operations', views.view_operations, name='operations'),
    path('suplies', views.view_suplies, name='suplies'),
    path('southdistrict', views.view_southdistrict, name='southdistrict'),
    
    
    path('southengineering', views.view_southengineering, name='southengineering'), 
    path('southglenview', views.view_southglenview, name='southglenview'),
    path('southwaterfalls', views.view_southwaterfalls, name='southwaterfalls'),
    path('southsales', views.view_southsales, name='southsales'),
    path('northdistrict', views.view_northdistrict, name='northdistrict'),
    path('northkuwadzana', views.view_northkuwadzana, name='northkuwadzana'),
    path('northmabelreign', views.view_northmabelreign, name='northmabelreign'),
    path('northwarrenpark', views.view_northwarrenpark, name='northwarrenpark'),
    path('northsales', views.view_northsales, name='northsales'),
    path('eastdistrict', views.view_eastdistrict, name='eastdistrict'),
    path('eastcbd', views.view_eastcbd, name='eastcbd'),
    path('eastruwa', views.view_eastruwa, name='eastruwa'),
    path('eastborrowdale', views.view_eastborrowdale, name='eastborrowdale'),
    path('eastmabvuku', views.view_eastmabvuku, name='eastmabvuku'),
    path('chitownsales', views.view_chitownsales, name='chitownsales'),
    path('chitownzengeza', views.view_chitownzengeza, name='chitownzengeza'),
    path('chitownseke', views.view_chitownseke, name='chitownseke'),
    path('chitowndistrict', views.view_chitowndistrict, name='chitowndistrict'),
    path('itjobdescription', views.view_itjobdescription, name='itjobdescription'),
    path('procjobdescription', views.view_procjobdescription, name='procjobdescription'),
    path('srjobdescription', views.view_srjobdescription, name='srjobdescription'),
    path('riskjobdescription', views.view_riskjobdescription, name='riskjobdescription'),
    path('legaljobdescription', views.view_legaljobdescription, name='legaljobdescription'),
    path('hrjobdescription', views.view_hrjobdescription, name='hrjobdescription'),
    path('finjobdescription', views.view_finjobdescription, name='finjobdescription'),
    path('engjobdescription', views.view_engjobdescription, name='engjobdescription'),
    path('comjobdescription', views.view_comjobdescription, name='comjobdescription'),
    path('eastengineering', views.view_eastengineering, name='eastengineering'),
    path('easternregion', views.view_easternregion, name='easternregion'),
    path('chitownengineering', views.view_chitownengineering, name='chitownengineering'),
    path('northengineering', views.view_northengineering, name='northengineering'),
    path('southertoncommercial', views.view_southertoncommercial, name='southertoncommercial'),
    path('rfqview',views.view_rfqview, name='rfqview'),
    path('job_upload', views.Job_description, name='job_upload'),






]
