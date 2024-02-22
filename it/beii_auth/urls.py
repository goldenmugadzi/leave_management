from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('business-applications', views.business_applications, name='business_applications'),
    path('home', views.home, name='home'),
    path('logout', views.app_logout, name='app_logout'),
]