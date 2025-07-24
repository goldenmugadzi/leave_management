from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('business-applications', views.business_applications, name='business_applications'),
    path('application-reports', views.application_reports, name='application_reports'),
    path('home', views.home, name='home'),
    path('logout', views.app_logout, name='app_logout'),
    path('auth/change-password', views.change_password, name='auth_change_password'),
    path('auth/answer-security-questions', views.security_questions, name='answer-security-questions'),
    path('auth/reset-after-verification', views.reset_password_after_verification, name='reset-after-verification'),
    path('auth/change-password/email', views.reset_email, name='reset_email'),
    path('auth/reset-password', views.reset_password, name='reset_password'),
    path('accounts/login/', views.login_user, name='login_user'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete_view, name='password_reset_complete'),
    path('test-email/', views.test_email, name='test_email'),
]