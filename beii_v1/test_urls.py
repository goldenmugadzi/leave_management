from django.urls import path, include

urlpatterns = [
    path('ace/', include('ACE2.urls')),
    path('pettycash/', include('finance.PettyCash.urls')),
]
