import re

from django.urls import reverse

from applications.models import Application
from applications.services import create_application, move_application
from candidates.tests.factories import CandidateFactory
from conftest import UserFactory
from jobs.tests.factories import JobOpeningFactory

Stage = Application.Stage

ROW = re.compile(r"<li data-history-row[^>]*>(.*?)</li>", re.S)


def timeline_rows(html):
    """The plain text of each timeline row on the page, in the order shown."""
    return [" ".join(re.sub(r"<[^>]+>", " ", row).split()) for row in ROW.findall(html)]


def test_timeline_lists_every_history_row_in_order_starting_with_recorded(logged_in_client):
    alice = UserFactory(username="alice")
    bob = UserFactory(username="bob")
    application = create_application(
        candidate=CandidateFactory(first_name="Ada", last_name="Lovelace"),
        job=JobOpeningFactory(),
        source=Application.Source.REFERRAL,
        user=alice,
    )
    move_application(application, to_stage=Stage.SCREENING, user=bob)
    move_application(application, to_stage=Stage.INTERVIEW, user=alice)

    response = logged_in_client.get(reverse("applications:detail", args=[application.pk]))

    assert response.status_code == 200
    rows = timeline_rows(response.content.decode())
    assert len(rows) == 3
    assert "Recorded" in rows[0] and "Applied" in rows[0] and "alice" in rows[0]
    assert "Applied" in rows[1] and "Screening" in rows[1] and "bob" in rows[1]
    assert "Screening" in rows[2] and "Interview" in rows[2] and "alice" in rows[2]


def test_reasons_for_past_rejections_and_withdrawals_stay_visible_after_reopening(
    logged_in_client, staff_user
):
    application = create_application(
        candidate=CandidateFactory(),
        job=JobOpeningFactory(),
        source=Application.Source.JOB_BOARD,
        user=staff_user,
    )
    move_application(
        application, to_stage=Stage.REJECTED, user=staff_user, reason="Missing SQL experience"
    )
    move_application(
        application, to_stage=Stage.APPLIED, user=staff_user, reason="Completed a SQL course"
    )
    move_application(
        application, to_stage=Stage.WITHDRAWN, user=staff_user, reason="Accepted another offer"
    )
    move_application(
        application, to_stage=Stage.APPLIED, user=staff_user, reason="Other offer fell through"
    )

    response = logged_in_client.get(reverse("applications:detail", args=[application.pk]))

    rows = timeline_rows(response.content.decode())
    assert len(rows) == 5
    assert "Rejected" in rows[1] and "Missing SQL experience" in rows[1]
    assert "Completed a SQL course" in rows[2]
    assert "Withdrawn" in rows[3] and "Accepted another offer" in rows[3]
    assert "Other offer fell through" in rows[4]


def test_page_shows_current_stage_job_and_source(logged_in_client, staff_user):
    application = create_application(
        candidate=CandidateFactory(first_name="Ada", last_name="Lovelace"),
        job=JobOpeningFactory(title="Data Analyst", department="Analytics", location="Remote"),
        source=Application.Source.REFERRAL,
        source_note="Referred by Maria",
        user=staff_user,
    )
    move_application(application, to_stage=Stage.SCREENING, user=staff_user)

    response = logged_in_client.get(reverse("applications:detail", args=[application.pk]))

    html = response.content.decode()
    assert "Ada Lovelace" in html
    assert "Data Analyst" in html and "Analytics · Remote" in html
    assert "Referral" in html and "Referred by Maria" in html
    assert re.search(r'id="current-stage"[^>]*>\s*Screening\s*</span>', html)
    assert reverse("applications:board", args=[application.job.pk]) in html


def test_deactivated_staff_stay_named_on_their_history_rows(logged_in_client):
    departed = UserFactory(username="departed", first_name="Dana", last_name="Gone")
    application = create_application(
        candidate=CandidateFactory(),
        job=JobOpeningFactory(),
        source=Application.Source.OTHER,
        user=departed,
    )
    move_application(application, to_stage=Stage.REJECTED, user=departed, reason="Not a fit")
    departed.is_active = False
    departed.save()

    response = logged_in_client.get(reverse("applications:detail", args=[application.pk]))

    rows = timeline_rows(response.content.decode())
    assert len(rows) == 2
    for row in rows:
        assert "Dana Gone" in row and "deactivated" in row


def test_detail_requires_login(client, db, staff_user):
    application = create_application(
        candidate=CandidateFactory(),
        job=JobOpeningFactory(),
        source=Application.Source.OTHER,
        user=staff_user,
    )
    url = reverse("applications:detail", args=[application.pk])

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={url}"


def test_detail_for_a_missing_application_is_404(logged_in_client):
    response = logged_in_client.get(reverse("applications:detail", args=[999999]))

    assert response.status_code == 404


def test_candidate_panel_and_board_cards_link_to_the_detail_page(logged_in_client, staff_user):
    application = create_application(
        candidate=CandidateFactory(),
        job=JobOpeningFactory(),
        source=Application.Source.OTHER,
        user=staff_user,
    )
    detail_url = reverse("applications:detail", args=[application.pk])

    panel = logged_in_client.get(
        reverse("applications:candidate_applications", args=[application.candidate.pk]),
        HTTP_HX_REQUEST="true",
    )
    board = logged_in_client.get(reverse("applications:board", args=[application.job.pk]))

    assert f'href="{detail_url}"' in panel.content.decode()
    assert f'href="{detail_url}"' in board.content.decode()
