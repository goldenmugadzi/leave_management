from django.urls import include, path

urlpatterns = [
    path('', include(('fault_locator.urls', 'fault_locator'), namespace='fault_locator')),
]
