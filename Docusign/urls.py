from django.urls import path
from .views import *
app_name = 'docusign' # Recommended: Namespace for better URL management

urlpatterns = [
    path('new_docusign_request/', SignatureRequestView.as_view(), name='new_docusign_request'),
    path('user-search/', UserSearchView.as_view(), name='user_search'),
    path('requests/', RequestListView.as_view(), name='request_list'),
    path('request/<int:pk>/', RequestDetailView.as_view(), name='request_detail'),
    path('download-with-qr/<int:request_id>/', download_with_qr, name='download_with_qr'),
    
    path("preview/<int:req_id>/", PDFPreviewView.as_view(), name="pdf_preview"),

    path('request/<int:pk>/sign/', RequestSignView.as_view(), name='request_sign'),
    # view a document inline (streams PDF with inline disposition)
    path('document/<int:pk>/view/', DocumentView.as_view(), name='document_view'),
    # signature upload endpoints
    path('signature/upload/', SignatureUploadView.as_view(), name='signature_upload'),
    path('signature/upload_canvas/', SignatureCanvasUploadView.as_view(), name='signature_upload_canvas'),
    path('apply_signature/', ApplySignatureView.as_view(), name='apply_signature'),
    # serve individual PDF pages rendered to images
    path('document/<int:pk>/page/<int:page>/image/', DocumentPageImageView.as_view(), name='document_page_image'),
]