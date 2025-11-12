"""beiimain URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from it.users.serializers import MyTokenObtainPairView
from graphene_file_upload.django import FileUploadGraphQLView
from it.users.serializers import MyTokenObtainPairView

# Serve robots.txt to prevent search engine indexing
def robots_txt(request):
    robots_content = """# Robots.txt - Prevent search engine indexing
# This file blocks all web crawlers from indexing the site
# to prevent sensitive information disclosure

User-agent: *
Disallow: /

# Additional security measures:
# - No crawling of any part of the site
# - No indexing of file download endpoints
# - No crawling of user-generated content
# - No indexing of PII-containing documents

# This is a private business application containing sensitive data
# All access should be authenticated and authorized"""
    return HttpResponse(robots_content, content_type='text/plain')

urlpatterns = [
    path('robots.txt', robots_txt, name='robots_txt'),
    path('', include('pretask_risk_assessment.urls')),
    path('', include('it.beii_auth.urls')),
    path('', include('Docs.urls')),
    path('', include('tokens.urls')),
    # path('', include('esearch.urls')),
    path('', include('risk.audit.nonconformity.urls')),
    path('', include('finance.purchase_request.urls')),
    path('', include('approve.urls')),
    path('meter/', include('commecial.tempertockens.urls')),
    path('users/', include('it.users.urls')),
    path('change_requests/', include('it.change_requests.urls')),
    path('dashboards/', include('executive.general_dashboards.urls')),
    path('ims/', include('knowledge_center.urls')),
    path('ims/v2/', include('process_management.urls'), name='process_management'),
    path('processes/', include('processes.urls'), name='processes'),
    path('process_risks/', include('process_risks.urls'), name='process_risks'),
    # path('process_maps/',include('process_maps.urls'), name='process_maps'),
    path('competence/', include('competence_building.urls')),
    path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('ace/', include('ACE2.urls')),
    path('appraisal/', include('appraisal.urls')),
    # Namespaced include so templates can reverse with 'fault_locator:<name>'
    path('fault_locator/', include(('fault_locator.urls', 'fault_locator'), namespace='fault_locator')),
   

    # path('ace/', include('finance.Ace.urls')),
    path('direct_purchases/', include('finance.Direct_purchases.urls')),
    path('pettycash/', include('finance.PettyCash.urls')),
    path('comperative_schedule/', include('finance.comparative_schedules.urls')),
    path('restricted_bidding/', include('finance.ristricted_bidding.urls')),
    path('direct_purchase/', include('finance.direct_purchase.urls')),
    path('reports/', include('reports.urls')),
    # OPS & MAINTENANCE
    path('api/safety/operations/', include('api.ops_maintenance.safety_operations.urls')),
     # path('', include('hardware_faults.urls')),
    path('', include('Hardware_Faults.urls')),
    path('', include('Asset_Register.urls')),

    # Add the comm_files app URLs
    path('commercial/', include('comm_files.urls')),
    path('', include('Transport.urls')),
    # path('', include('safety.urls')),
    # path('meetings/', include('meetings.urls')),
    path('search/', include('esearch.urls')),
    path('temp_tokens/', include('commecial.tempertockens.urls')),
    path('', include('EquipTracker.urls')),
    path('competence_building/', include('competence_building.urls')),
    # path('api/', include('api.urls')),  # Commented out until api.urls exists
    path('', include('meetings.urls')),
    path('', include('leave_management.urls')),
    path('', include('asset_transfer.urls')),
    path('', include('register.urls')),
    path('sanction_for_test/', include('sanction_for_test.urls')),
    path('inspections/', include('inspections.urls')),
    path('substation-inspections/', include('substation_inspections.urls')),
    path('e60-inspections/', include('e60_inspections.urls')),
    path('circuit-breakers/', include('circuit_breaker_maintenance.urls')),
    path('equipment/', include('equipment_management.urls')),
    
    path('api-auth/', include('rest_framework.urls')),
    path("gql/", csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))),  
    path('api/auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

] 
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
