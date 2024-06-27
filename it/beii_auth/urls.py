from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('business-applications', views.business_applications, name='business_applications'),
    path('home', views.home, name='home'),
    path('logout', views.app_logout, name='app_logout'),
    path('auth/change-password', views.change_password, name='auth_change_password'),
    path('auth/answer-security-questions', views.security_questions, name='answer-security-questions'),
    path('auth/change-password/email', views.reset_email, name='reset_email'),
    path('auth/reset-password', views.reset_password, name='reset_password'),
    
    
]