from django.urls import path
from .views import *

app_name = 'nonconformity'

urlpatterns = [
    path('create_nonconformity/', create_nonconformity, name='create_nonconformity'),
    path('create_nonconformity/<str:clause>', create_nonconformity_from_checklist, name='create_nonconformity_from_checklist'),
    path('inbox/', view_notifications, name='inbox'),
    path('nonconformities/', view_nonconformities, name='nonconformities'),
    path('my_nonconformities/', my_nonconformities, name='my_nonconformities'),
    path('nonconformity/<int:nonconformity_id>/', nonconformity_details, name='nonconformity'),
    path('create_clause/', ClauseCreateView.as_view(), name='create_clause'),
    path('<int:clause_id>/add-qns/', Question_formset_view, name='add-qns'),
    path('newinfo/<int:nonconformity_id>/', additionalInfoForm, name='newinfo'),
    path('checkist/', checklist, name='checklist'),
]