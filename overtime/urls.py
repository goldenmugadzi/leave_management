from django.urls import path
from . import views

app_name = "overtime"

urlpatterns = [
	path("create/", views.create_overtime_entry, name="create_entry"),
	path("success/", views.entry_success, name="entry_success"),
]