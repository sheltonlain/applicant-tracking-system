from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "applications/new/<int:candidate_pk>/",
        views.candidate_applications,
        name="candidate_applications",
    ),
]
