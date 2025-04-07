from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (CustomAuthToken, api_logout, current_user, AceViewSet, 
                 BudgetViewSet, TransactionViewSet, ViramentViewSet, 
                 SectionViewSet, RegionViewSet, my_actioned_items)

router = DefaultRouter()
router.register(r'aces', AceViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'viraments', ViramentViewSet)
router.register(r'sections', SectionViewSet)
router.register(r'regions', RegionViewSet)

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomAuthToken.as_view(), name='api_login'),
    path('auth/logout/', api_logout, name='api_logout'),
    path('auth/user/', current_user, name='current_user'),
    
    # Data retrieval and action endpoints
    path('', include(router.urls)),
    path('my-actioned-items/', my_actioned_items, name='api_my_actioned_items'),
]
