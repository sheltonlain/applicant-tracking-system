from django.contrib import admin

from .models import Candidate


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "email", "phone", "archived", "created_at"]
    list_filter = ["archived"]
    search_fields = ["first_name", "last_name", "email"]
    # Archiving changes only through the app's Archive / Unarchive buttons, because archiving
    # is blocked while the candidate has an active application.
    readonly_fields = ["archived"]
