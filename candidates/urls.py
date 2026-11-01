from django.urls import path

from . import views

app_name = "candidates"

urlpatterns = [
    path("new/", views.candidate_create, name="create"),
    path("<int:pk>/", views.candidate_detail, name="detail"),
    path("<int:pk>/edit/", views.candidate_edit, name="edit"),
]
