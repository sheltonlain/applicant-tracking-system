import pytest
from django.urls import get_resolver, reverse

from applications.models import Application, StageChange
from applications.services import (
    ApplicationError,
    ArchiveError,
    archive_candidate,
    create_application,
    move_application,
)
from applications.stages import ACTIVE_STAGES, FINAL_STAGES
from applications.tests.factories import ApplicationFactory
from candidates.models import Candidate
from candidates.tests.factories import CandidateFactory
from jobs.tests.factories import JobOpeningFactory

HTMX = {"HX-Request": "true"}


def archive_url(candidate):
    return reverse("applications:archive_candidate", args=[candidate.pk])


def panel_url(candidate):
    return reverse("applications:candidate_applications", args=[candidate.pk])


# --- Service ---------------------------------------------------------------------------------


@pytest.mark.parametrize("active_stage", ACTIVE_STAGES)
def test_archive_is_blocked_while_any_application_is_active_and_allowed_once_all_are_final(
    db, active_stage
):
    candidate = CandidateFactory()
    for final_stage in FINAL_STAGES:
        ApplicationFactory(candidate=candidate, stage=final_stage)
    still_active = ApplicationFactory(candidate=candidate, stage=active_stage)

    with pytest.raises(ArchiveError):
        archive_candidate(candidate)
    candidate.refresh_from_db()
    assert candidate.archived is False

    Application.objects.filter(pk=still_active.pk).update(stage=Application.Stage.WITHDRAWN)
    archive_candidate(candidate)
    candidate.refresh_from_db()
    assert candidate.archived is True


def test_a_candidate_with_no_applications_can_be_archived(db):
    candidate = CandidateFactory()

    archive_candidate(candidate)

    candidate.refresh_from_db()
    assert candidate.archived is True


def test_blocked_archive_message_says_how_many_applications_are_active(db):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe")
    ApplicationFactory.create_batch(2, candidate=candidate, stage=Application.Stage.INTERVIEW)

    with pytest.raises(ArchiveError, match="Jane Doe can't be archived while 2 applications"):
        archive_candidate(candidate)


def test_archiving_an_already_archived_candidate_is_refused(db):
    candidate = CandidateFactory(archived=True)

    with pytest.raises(ArchiveError, match="already archived"):
        archive_candidate(candidate)


def test_archiving_leaves_applications_and_history_unchanged(staff_user):
    candidate = CandidateFactory()
    application = create_application(
        candidate=candidate, job=JobOpeningFactory(), source="referral", user=staff_user
    )
    move_application(
        application, to_stage=Application.Stage.REJECTED, user=staff_user, reason="Not a fit"
    )
    before = list(StageChange.objects.values())

    archive_candidate(candidate)

    application.refresh_from_db()
    assert application.candidate == candidate
    assert application.stage == Application.Stage.REJECTED
    assert list(StageChange.objects.values()) == before


def test_create_application_refuses_an_archived_candidate(staff_user):
    candidate = CandidateFactory(archived=True)

    with pytest.raises(ApplicationError, match="archived"):
        create_application(
            candidate=candidate, job=JobOpeningFactory(), source="other", user=staff_user
        )
    assert not Application.objects.exists()


# --- Archive view ----------------------------------------------------------------------------


def test_archive_url_sits_with_the_candidates_other_urls(db):
    candidate = CandidateFactory()

    assert archive_url(candidate) == f"/candidates/{candidate.pk}/archive/"


def test_archive_button_archives_and_returns_to_the_candidate_page(logged_in_client):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe")

    response = logged_in_client.post(archive_url(candidate), follow=True)

    candidate.refresh_from_db()
    assert candidate.archived is True
    assert response.redirect_chain[-1][0] == candidate.get_absolute_url()
    assert "Jane Doe archived" in response.content.decode()


def test_blocked_archive_shows_a_clear_message_and_changes_nothing(logged_in_client):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe")
    ApplicationFactory(candidate=candidate, stage=Application.Stage.OFFER)

    response = logged_in_client.post(archive_url(candidate), follow=True)

    candidate.refresh_from_db()
    assert candidate.archived is False
    assert response.status_code == 200
    page = response.content.decode()
    assert "Jane Doe can&#x27;t be archived while 1 application is still active" in page


def test_archiving_twice_shows_a_friendly_note(logged_in_client):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe", archived=True)

    response = logged_in_client.post(archive_url(candidate), follow=True)

    assert response.status_code == 200
    assert "Jane Doe is already archived." in response.content.decode()


def test_archive_only_accepts_post(logged_in_client):
    candidate = CandidateFactory()

    assert logged_in_client.get(archive_url(candidate)).status_code == 405
    candidate.refresh_from_db()
    assert candidate.archived is False


def test_archive_requires_login(client, db):
    candidate = CandidateFactory()

    response = client.post(archive_url(candidate))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
    candidate.refresh_from_db()
    assert candidate.archived is False


# --- Candidate page --------------------------------------------------------------------------


def test_add_application_endpoint_refuses_an_archived_candidate(logged_in_client):
    candidate = CandidateFactory(archived=True)
    job = JobOpeningFactory()

    logged_in_client.post(
        panel_url(candidate),
        {"job": job.pk, "source": Application.Source.JOB_BOARD},
        headers=HTMX,
    )

    assert not Application.objects.exists()
    assert not StageChange.objects.exists()


def test_refused_add_application_reloads_the_page_with_a_note(logged_in_client):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe", archived=True)

    response = logged_in_client.post(
        panel_url(candidate), {"job": JobOpeningFactory().pk, "source": "other"}, headers=HTMX
    )

    assert response["HX-Redirect"] == candidate.get_absolute_url()
    page = logged_in_client.get(candidate.get_absolute_url()).content.decode()
    assert "Jane Doe is archived, so new applications can&#x27;t be added." in page


def test_archived_candidate_panel_lists_applications_but_has_no_add_form(logged_in_client):
    candidate = CandidateFactory(archived=True)
    ApplicationFactory(
        candidate=candidate, job=JobOpeningFactory(title="Data Analyst"), stage="hired"
    )
    JobOpeningFactory(title="Open Role")  # would be offered to a candidate who isn't archived

    panel = logged_in_client.get(panel_url(candidate), headers=HTMX).content.decode()

    assert "Data Analyst" in panel
    assert 'name="job"' not in panel
    assert "Add application" not in panel
    assert "Archived candidates can't get new applications" in panel


def test_candidate_page_offers_archive_to_a_current_candidate(logged_in_client):
    candidate = CandidateFactory()

    page = logged_in_client.get(candidate.get_absolute_url()).content.decode()

    assert f'action="{archive_url(candidate)}"' in page
    assert reverse("candidates:unarchive", args=[candidate.pk]) not in page


def test_the_app_has_no_url_for_deleting_a_candidate():
    # Only the admin can delete, and PROTECT stops it for anyone with applications.
    for namespace in ["candidates", "applications"]:
        _, app_resolver = get_resolver().namespace_dict[namespace]
        names = [name for name in app_resolver.reverse_dict if isinstance(name, str)]
        assert names  # the namespace's URLs were found
        assert not [name for name in names if "delete" in name], namespace


def test_archived_candidate_still_exists_after_archive_and_unarchive(logged_in_client):
    candidate = CandidateFactory()

    logged_in_client.post(archive_url(candidate))
    logged_in_client.post(reverse("candidates:unarchive", args=[candidate.pk]))

    assert Candidate.objects.filter(pk=candidate.pk, archived=False).exists()
