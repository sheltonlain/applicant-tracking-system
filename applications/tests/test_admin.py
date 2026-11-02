from django.urls import reverse

from applications.models import Application
from applications.tests.factories import StageChangeFactory
from conftest import UserFactory


def test_admin_shows_history_read_only_and_cannot_add_delete_or_change_stage(client, db):
    client.force_login(UserFactory(is_staff=True, is_superuser=True))
    change = StageChangeFactory()
    application = change.application

    change_page = client.get(
        reverse("admin:applications_application_change", args=[application.pk])
    )
    add_page = client.get(reverse("admin:applications_application_add"))
    delete = client.post(
        reverse("admin:applications_application_delete", args=[application.pk]), {"post": "yes"}
    )
    client.post(
        reverse("admin:applications_application_change", args=[application.pk]),
        {
            "source": "other",
            "source_note": "fixed",
            "stage": Application.Stage.HIRED,  # not an editable field, so it must be ignored
            # The read-only history inline's management form, as the browser would send it.
            "stage_changes-TOTAL_FORMS": "1",
            "stage_changes-INITIAL_FORMS": "1",
            "stage_changes-0-id": change.pk,
            "stage_changes-0-application": application.pk,
        },
    )

    assert change_page.status_code == 200
    assert change.user.username in change_page.content.decode()
    assert 'name="stage"' not in change_page.content.decode()
    assert add_page.status_code == 403
    assert delete.status_code == 403
    application.refresh_from_db()
    assert application.stage == Application.Stage.APPLIED  # stage ignored
    assert application.source_note == "fixed"  # source can be corrected
