from django.urls import path
from .views import SignatureRequestView, UserSearchView

app_name = 'docusign' # Recommended: Namespace for better URL management

urlpatterns = [
    path('new_docusign_request/',SignatureRequestView.as_view(),name='new_docusign_request'),
    path('user-search/', UserSearchView.as_view(), name='user_search'),
]