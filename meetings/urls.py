from django.urls import path
from . import views

urlpatterns = [
    path('meetings/create/', views.create_meeting, name='create_meeting_with_booking'),
    path('meetings_datatable/', views.meetings_datatable, name='meetings_datatable'),
    path('table_meeting/', views.table_meetings, name="table_meeting"),
    path('update_meeting/<int:id>/', views.update_meeting, name='update_meeting'),
    path('meetings_dashboard/', views.meetings_dashboard, name='meetings_dashboard'),
    path('book_venue/', views.create_venue_booking, name='create_venue_booking'),
    path('venues_datatable/', views.venues_datatable, name='venues_datatable'),
    path('booked_venue/', views.booked_venue, name='booked_venue'),
    path('booked_venues_datatable/', views.booked_venues_datatable, name='booked_venues_datatable'),
    path("venue-booking/<int:pk>/update/", views.update_venue_booking, name="update_venue_booking"),
]