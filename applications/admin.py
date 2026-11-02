from django.contrib import admin

from .models import Application, StageChange


class StageChangeInline(admin.TabularInline):
    # History is written only by the applications services; the admin shows it read-only.
    model = StageChange
    extra = 0
    fields = ["changed_at", "from_stage", "to_stage", "user", "reason"]
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["candidate", "job", "stage", "source", "created_at"]
    list_filter = ["stage", "source"]
    search_fields = ["candidate__first_name", "candidate__last_name", "candidate__email"]
    list_select_related = ["candidate", "job"]
    # Applications are added from the candidate page and stages change only through the
    # services, so each one gets its history row. Here only the source can be corrected.
    fields = ["candidate", "job", "source", "source_note", "stage", "created_at", "updated_at"]
    readonly_fields = ["candidate", "job", "stage", "created_at", "updated_at"]
    inlines = [StageChangeInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Deleting an application would delete its history, which must be permanent.
        return False
