from django.urls import path
from .views import *

urlpatterns = [
 
    path('search/', search_view, name='search'),
    path('fscrawler/', start_fscrawler, name='fscrawler'),
     path('pdf/', view_pdf, name='view_pdf'),
    # path('upload/', upload_file, name='upload_file'),
]