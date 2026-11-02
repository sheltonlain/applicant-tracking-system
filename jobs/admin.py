from django.contrib import admin

from .models import JobOpening, JobSkill, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    # Skill.clean() refuses names that differ only in case; JobSkill's PROTECT blocks deleting
    # a skill that a job still uses.
    search_fields = ["name"]


class JobSkillInline(admin.TabularInline):
    # The skills link uses a custom table, which the admin can't show as a plain field.
    model = JobSkill
    extra = 0
    autocomplete_fields = ["skill"]
    verbose_name = "skill"


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "location", "employment_type", "status", "created_at"]
    list_filter = ["status", "employment_type"]
    search_fields = ["title", "department", "location"]
    # Status and closed-at change only through the app's Close / Reopen buttons (jobs.services).
    readonly_fields = ["status", "closed_at"]
    inlines = [JobSkillInline]
