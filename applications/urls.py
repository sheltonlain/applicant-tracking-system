from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("applications/board/<int:job_pk>/", views.board, name="board"),
    path("applications/<int:pk>/move/", views.move, name="move"),
    path("applications/<int:pk>/move/dialog/", views.move_dialog, name="move_dialog"),
    path(
        "applications/new/<int:candidate_pk>/",
        views.candidate_applications,
        name="candidate_applications",
    ),
]
