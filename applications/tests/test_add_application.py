import ast
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

from applications.models import Application, StageChange
from applications.tests.factories import ApplicationFactory
from candidates.tests.factories import CandidateFactory
from jobs.models import JobOpening
from jobs.tests.factories import JobOpeningFactory

HTMX = {"HX-Request": "true"}


def panel_url(candidate):
    return reverse("applications:candidate_applications", args=[candidate.pk])


def test_candidate_page_lazy_loads_the_applications_panel(logged_in_client, db):
    candidate = CandidateFactory()

    page = logged_in_client.get(reverse("candidates:detail", args=[candidate.pk])).content.decode()

    assert f'hx-get="{panel_url(candidate)}"' in page
    assert 'hx-trigger="load"' in page


def test_panel_lists_applications_with_job_details_stage_and_source(logged_in_client, db):
    candidate = CandidateFactory()
    job = JobOpeningFactory(title="Data Analyst", department="Finance", location="Austin")
    ApplicationFactory(
        candidate=candidate,
        job=job,
        stage=Application.Stage.INTERVIEW,
        source=Application.Source.REFERRAL,
        source_note="Referred by Maria",
    )
    ApplicationFactory(job=JobOpeningFactory(title="Someone Else's Job"))

    panel = logged_in_client.get(panel_url(candidate), headers=HTMX).content.decode()
    application_list = panel.split("Add application")[0]  # the table, not the job dropdown

    for text in ["Data Analyst", "Finance · Austin", "Interview", "Referral", "Referred by Maria"]:
        assert text in application_list
    assert "Someone Else&#x27;s Job" not in application_list
    assert "<html" not in panel  # only the panel, not a whole page


def test_panel_job_choices_exclude_closed_and_already_applied_jobs(logged_in_client, db):
    candidate = CandidateFactory()
    JobOpeningFactory(title="Open Role")
    JobOpeningFactory(title="Closed Role", status=JobOpening.Status.CLOSED)
    ApplicationFactory(candidate=candidate, job=JobOpeningFactory(title="Applied Role"))

    panel = logged_in_client.get(panel_url(candidate), headers=HTMX).content.decode()
    options = panel.split('name="job"')[1].split("</select>")[0]

    assert "Open Role" in options
    assert "Closed Role" not in options
    assert "Applied Role" not in options


def test_panel_says_so_when_no_jobs_are_left_to_apply_to(logged_in_client, db):
    candidate = CandidateFactory()
    JobOpeningFactory(status=JobOpening.Status.CLOSED)

    panel = logged_in_client.get(panel_url(candidate), headers=HTMX).content.decode()

    assert 'name="job"' not in panel
    assert "no open jobs" in panel


def test_posting_the_form_records_the_application_and_reloads_the_candidate_page(
    logged_in_client, staff_user
):
    candidate = CandidateFactory()
    job = JobOpeningFactory(title="Data Analyst")

    response = logged_in_client.post(
        panel_url(candidate),
        {"job": job.pk, "source": Application.Source.JOB_BOARD, "source_note": "LinkedIn"},
        headers=HTMX,
    )

    assert response["HX-Redirect"] == candidate.get_absolute_url()
    application = Application.objects.get(candidate=candidate, job=job)
    assert application.stage == Application.Stage.APPLIED
    assert application.source == Application.Source.JOB_BOARD
    assert application.source_note == "LinkedIn"
    assert application.stage_changes.get().user == staff_user

    page = logged_in_client.get(candidate.get_absolute_url()).content.decode()
    assert "Application to Data Analyst" in page  # the success message


def test_form_errors_are_shown_in_the_panel_and_nothing_is_saved(logged_in_client, db):
    candidate = CandidateFactory()
    closed_job = JobOpeningFactory(status=JobOpening.Status.CLOSED)
    JobOpeningFactory()  # so the form is still shown

    response = logged_in_client.post(
        panel_url(candidate), {"job": closed_job.pk, "source": ""}, headers=HTMX
    )

    panel = response.content.decode()
    assert response.status_code == 200
    assert "HX-Redirect" not in response
    assert "Select a valid choice" in panel  # a crafted post for a closed job
    assert "This field is required" in panel  # source
    assert not Application.objects.exists()
    assert not StageChange.objects.exists()


def test_direct_visit_to_the_panel_redirects_to_the_candidate_page(logged_in_client, db):
    candidate = CandidateFactory()

    response = logged_in_client.get(panel_url(candidate))

    assert response.status_code == 302
    assert response.url == candidate.get_absolute_url()


@pytest.mark.parametrize("method", ["get", "post"])
def test_panel_requires_login(client, db, method):
    candidate = CandidateFactory()
    job = JobOpeningFactory()

    response = getattr(client, method)(
        panel_url(candidate), {"job": job.pk, "source": "other"}, headers=HTMX
    )

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
    assert not Application.objects.exists()


def test_candidates_and_jobs_apps_never_import_from_applications():
    for app in ["candidates", "jobs"]:
        for path in (Path(settings.BASE_DIR) / app).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                elif isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                else:
                    continue
                for module in modules:
                    assert module.split(".")[0] != "applications", f"{path} imports {module}"
