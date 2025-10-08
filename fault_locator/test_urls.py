from django.urls import path, include
from fault_locator import views as flviews

fl_patterns = [
    path('cranes/trucks/create/', flviews.crane_truck_create, name='crane_truck_create'),
    path('cranes/trucks/', flviews.crane_truck_list, name='crane_truck_list'),
    path('cranes/trucks/<int:truck_id>/edit/', flviews.crane_truck_edit, name='crane_truck_edit'),
    path('cranes/requests/create/', flviews.crane_request_create, name='crane_request_create'),
    path('cranes/requests/', flviews.crane_request_list, name='crane_request_list'),
    path('cranes/requests/<int:request_id>/assign/', flviews.crane_request_assign, name='crane_request_assign'),
    path('cranes/requests/<int:request_id>/report/', flviews.crane_job_report, name='crane_job_report'),
    path('dashboard/', flviews.fault_locator_dashboard, name='fault_locator_dashboard'),
]

urlpatterns = [
    path('', include((fl_patterns, 'fault_locator'), namespace='fault_locator')),
]

# Also expose the same patterns without a namespace to support tests that
# reverse URLs without the 'fault_locator:' prefix.
urlpatterns += fl_patterns
