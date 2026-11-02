from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("applications/board/<int:job_pk>/", views.board, name="board"),
    path("applications/board/<int:job_pk>/warning/", views.job_warning, name="job_warning"),
    path("applications/<int:pk>/", views.detail, name="detail"),
    path("applications/<int:pk>/move/", views.move, name="move"),
    path("applications/<int:pk>/move/dialog/", views.move_dialog, name="move_dialog"),
    path(
        "applications/new/<int:candidate_pk>/",
        views.candidate_applications,
        name="candidate_applications",
    ),
    # Under /candidates/ to match the candidate's other URLs, but served by this app, because
    # the archive rule depends on the candidate's applications.
    path(
        "candidates/<int:candidate_pk>/archive/",
        views.candidate_archive,
        name="archive_candidate",
    ),
]
