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
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [
    path('', include('it.beii_auth.urls')),
    path('', include('Docs.urls')),
    path('', include('tokens.urls')),
    path('', include('esearch.urls')),
    path('', include('risk.audit.nonconformity.urls')),
    path('', include('finance.purchase_request.urls')),
    path('', include('approve.urls')),
    path('meter/', include('commecial.tempertockens.urls')),
    path('users/', include('it.users.urls')),
    path('change_requests/', include('it.change_requests.urls')),
    path('dashboards/', include('executive.exec_dashboards.urls')),
    path('knowledge_center/', include('knowledge_center.urls')),
    path('processes/', include('processes.urls'), name='processes'),
    path('process_risks/', include('process_risks.urls'), name='process_risks'),
    # path('process_maps/',include('process_maps.urls'), name='process_maps'),
    path('competence/', include('competence_building.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('ace/', include('ACE2.urls')),

    # path('ace/', include('finance.Ace.urls')),
    path('direct_purchases/', include('finance.Direct_purchases.urls')),
    path('pettycash/', include('finance.PettyCash.urls')),
    path('comperative_schedule/', include('finance.comparative_schedules.urls')),
    path('ristricted_bidding/', include('finance.ristricted_bidding.urls')),
    path('direct_purchase/', include('finance.direct_purchase.urls')),
    path('reports/', include('reports.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

] 
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
