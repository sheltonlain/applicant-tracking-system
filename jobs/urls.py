from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("new/", views.job_create, name="create"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("<int:pk>/edit/", views.job_edit, name="edit"),
    path("<int:pk>/close/", views.job_close, name="close"),
    path("<int:pk>/reopen/", views.job_reopen, name="reopen"),
    path("skills/", views.skill_list, name="skill_list"),
    path("skills/add/", views.skill_add, name="skill_add"),
    path("skills/<int:pk>/edit/", views.skill_edit, name="skill_edit"),
    path("skills/<int:pk>/delete/", views.skill_delete, name="skill_delete"),
]
