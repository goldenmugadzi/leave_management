from django.urls import path
from .views import *

app_name ='tokens'

urlpatterns = [
     path('create_token/', create_token, name='create_token'),
    path('token/<str:token_id>/', token_details, name='token'),
    path('tokens/', view_all_tokens, name='tokens'),
    path('tokens_reports/', tokens_reports, name='tokens_reports'),
    path('addsection/', addsection, name='addsection'),
    path('tokens_awaiting_my_action/', awaiting_my_action, name='tokens_awaiting_my_action'),
    path('upload_centers/', upload_centers, name='upload_centers'),
    path('cost_centers/', cost_centers, name='cost_centers'),
    path('cost_center/<str:cost_center_id>/', cost_center, name='cost_center'),
    path('migrate_tokens/', migrate_tokens, name='migrate_tokens'),
    path('migrate_reimbursement_tokens/', migrate_reimbursement_tokens, name='migrate_reimbursement_tokens'),
    path('migrate_clear_credit_tokens/', migrate_clear_credit_tokens, name='migrate_clear_credit_tokens'),
    path('api/create-token/', create_token_api, name='create_token_api'),
    path('api/view-token/<str:token_id>/', view_token_api, name='view_token_api'),
]
