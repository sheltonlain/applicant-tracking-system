from django.urls import path

from . import views

app_name = "candidates"

urlpatterns = [
    path("", views.candidate_list, name="list"),
    path("new/", views.candidate_create, name="create"),
    path("<int:pk>/", views.candidate_detail, name="detail"),
    path("<int:pk>/edit/", views.candidate_edit, name="edit"),
    path("<int:pk>/resume/", views.resume_download, name="resume"),
    path("<int:pk>/resume/upload/", views.resume_upload, name="resume_upload"),
]
