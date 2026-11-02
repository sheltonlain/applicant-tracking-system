from django.contrib import admin

from .models import JobOpening


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "location", "employment_type", "status", "created_at"]
    list_filter = ["status", "employment_type"]
    search_fields = ["title", "department", "location"]
    # Status and closed-at change only through the app's Close / Reopen buttons (jobs.services).
    readonly_fields = ["status", "closed_at"]
