import re

import pytest
from django.urls import reverse

from applications.models import Application
from applications.tests.factories import ApplicationFactory, StageChangeFactory
from applications.tests.test_board import board_columns_in, card_targets
from jobs.models import JobOpening
from jobs.tests.factories import JobOpeningFactory

Stage = Application.Stage


def test_htmx_blank_reason_redraws_the_dialog_with_the_error_and_leaves_the_board(
    logged_in_client, staff_user
):
    application = ApplicationFactory(stage=Stage.INTERVIEW)
    StageChangeFactory(
        application=application, from_stage="", to_stage=Stage.APPLIED, user=staff_user
    )

    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"to_stage": Stage.REJECTED, "reason": "   "},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    # The response replaces the dialog, not the board.
    assert response.get("HX-Retarget") == "#move-dialog"
    assert response.get("HX-Reswap") == "innerHTML"
    html = response.content.decode()
    assert 'id="board"' not in html
    assert 'class="modal modal-open"' in html
    assert "A reason is required" in html
    assert f'name="to_stage" value="{Stage.REJECTED}"' in html
    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW
    assert application.stage_changes.count() == 1


@pytest.mark.parametrize(
    ("stage", "to_stage", "title", "asks_reason", "submit_label"),
    [
        (Stage.INTERVIEW, Stage.REJECTED, "Reject Ann Lee?", True, "Reject"),
        (Stage.INTERVIEW, Stage.WITHDRAWN, "Withdraw Ann Lee?", True, "Withdraw"),
        (Stage.REJECTED, Stage.INTERVIEW, "Reopen Ann Lee?", True, "Reopen to Interview"),
        (Stage.OFFER, Stage.HIRED, "Mark Ann Lee as Hired?", False, "Mark Hired"),
    ],
)
def test_dialog_url_returns_the_modal_for_an_allowed_move(
    logged_in_client, staff_user, stage, to_stage, title, asks_reason, submit_label
):
    application = ApplicationFactory(
        stage=stage, candidate__first_name="Ann", candidate__last_name="Lee"
    )
    if stage == Stage.REJECTED:
        StageChangeFactory(
            application=application,
            from_stage=Stage.INTERVIEW,
            to_stage=Stage.REJECTED,
            user=staff_user,
        )

    response = logged_in_client.get(
        reverse("applications:move_dialog", args=[application.pk]),
        {"to_stage": to_stage},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'class="modal modal-open"' in html
    assert 'id="board"' not in html
    assert title in html
    assert f'name="to_stage" value="{to_stage}"' in html
    assert f'hx-post="{reverse("applications:move", args=[application.pk])}"' in html
    assert ('name="reason"' in html) == asks_reason
    assert submit_label in html
    application.refresh_from_db()
    assert application.stage == stage  # opening a dialog never moves anything


def test_closed_column_cards_show_the_stage_they_were_closed_from(logged_in_client, staff_user):
    job = JobOpeningFactory()
    rejected = ApplicationFactory(job=job, stage=Stage.REJECTED, candidate__last_name="Rejectson")
    withdrawn = ApplicationFactory(
        job=job, stage=Stage.WITHDRAWN, candidate__last_name="Withdrawson"
    )
    ApplicationFactory(job=job, stage=Stage.HIRED, candidate__last_name="Hiredson")
    StageChangeFactory(
        application=rejected, from_stage=Stage.INTERVIEW, to_stage=Stage.REJECTED, user=staff_user
    )
    StageChangeFactory(
        application=withdrawn,
        from_stage=Stage.SCREENING,
        to_stage=Stage.WITHDRAWN,
        user=staff_user,
    )

    response = logged_in_client.get(reverse("applications:board", args=[job.pk]))

    closed = " ".join(board_columns_in(response.content.decode())["closed"][1].split())
    assert "Rejected · from Interview" in closed
    assert "Withdrawn · from Screening" in closed
    assert "Hired · from" not in closed  # Hired isn't closed *from* anywhere; it's final


def dialog_targets(html):
    """The to_stage values of every dialog-opening button drawn in some HTML."""
    return re.findall(r'hx-get="[^"]*/move/dialog/\?to_stage=(\w+)"', html)


def test_board_cards_offer_close_menu_mark_hired_reopen_and_a_hired_lock(
    logged_in_client, staff_user
):
    job = JobOpeningFactory()
    ApplicationFactory(job=job, stage=Stage.APPLIED)
    ApplicationFactory(job=job, stage=Stage.OFFER)
    rejected = ApplicationFactory(job=job, stage=Stage.REJECTED)
    StageChangeFactory(
        application=rejected, from_stage=Stage.INTERVIEW, to_stage=Stage.REJECTED, user=staff_user
    )
    ApplicationFactory(job=job, stage=Stage.HIRED)

    html = logged_in_client.get(reverse("applications:board", args=[job.pk])).content.decode()

    columns = board_columns_in(html)
    applied = columns["applied"][1]
    assert dialog_targets(applied) == [Stage.REJECTED, Stage.WITHDRAWN]
    assert "Close ▾" in applied and "Reject…" in applied and "Withdraw…" in applied
    # Offer: Mark Hired opens a confirmation; it never posts straight away.
    offer = columns["offer"][1]
    assert dialog_targets(offer) == [Stage.HIRED, Stage.REJECTED, Stage.WITHDRAWN]
    assert "Mark Hired…" in offer
    assert card_targets(offer) == [Stage.FINAL_REVIEW]
    # Closed column: Reopen (to the stage it was closed from) only; Hired is locked.
    closed = columns["closed"][1]
    assert dialog_targets(closed) == [Stage.INTERVIEW]
    assert "Reopen…" in closed and "Close ▾" not in closed
    assert "🔒 Hired" in closed


def test_successful_htmx_reject_redraws_the_board_and_closes_the_dialog(
    logged_in_client, staff_user
):
    job = JobOpeningFactory()
    application = ApplicationFactory(job=job, stage=Stage.INTERVIEW)

    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"to_stage": Stage.REJECTED, "reason": "Not enough SQL experience"},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert response.get("HX-Retarget") is None  # the normal #board swap
    html = response.content.decode()
    assert "modal-open" not in html  # the redrawn board has an empty dialog slot
    columns = board_columns_in(html)
    assert columns["interview"][0] == 0 and columns["closed"][0] == 1
    assert "from Interview" in columns["closed"][1]
    latest = application.stage_changes.last()
    assert (latest.to_stage, latest.reason, latest.user) == (
        Stage.REJECTED,
        "Not enough SQL experience",
        staff_user,
    )


def test_non_htmx_blank_reason_redirects_to_the_board_with_a_message(logged_in_client):
    application = ApplicationFactory(stage=Stage.INTERVIEW)

    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"to_stage": Stage.WITHDRAWN, "reason": ""},
        follow=True,
    )

    assert response.redirect_chain[-1][0] == reverse(
        "applications:board", args=[application.job.pk]
    )
    assert "A reason is required to move to Withdrawn." in response.content.decode()
    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW


@pytest.mark.parametrize(
    ("stage", "to_stage"),
    [
        (Stage.HIRED, Stage.OFFER),  # nothing moves out of Hired
        (Stage.INTERVIEW, Stage.OFFER),  # a skip
        (Stage.APPLIED, Stage.SCREENING),  # allowed, but a plain Advance needs no dialog
        (Stage.INTERVIEW, "banana"),
    ],
)
def test_dialog_for_a_move_without_a_dialog_redraws_the_board_with_a_note(
    logged_in_client, stage, to_stage
):
    application = ApplicationFactory(stage=stage)

    response = logged_in_client.get(
        reverse("applications:move_dialog", args=[application.pk]),
        {"to_stage": to_stage},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert response.get("HX-Retarget") == "#board"
    assert response.get("HX-Reswap") == "outerHTML"
    html = response.content.decode()
    assert 'id="board"' in html and "modal-open" not in html
    assert "That move is no longer available" in html
    application.refresh_from_db()
    assert application.stage == stage


def test_dialog_without_htmx_redirects_to_the_board(logged_in_client):
    application = ApplicationFactory(stage=Stage.INTERVIEW)

    response = logged_in_client.get(
        reverse("applications:move_dialog", args=[application.pk]), {"to_stage": Stage.REJECTED}
    )

    assert response.status_code == 302
    assert response.url == reverse("applications:board", args=[application.job.pk])


def test_dialog_refuses_post(logged_in_client):
    application = ApplicationFactory(stage=Stage.INTERVIEW)

    response = logged_in_client.post(
        reverse("applications:move_dialog", args=[application.pk]),
        {"to_stage": Stage.REJECTED, "reason": "x"},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 405
    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW


def test_dialog_requires_login(client, db):
    application = ApplicationFactory(stage=Stage.INTERVIEW)
    url = reverse("applications:move_dialog", args=[application.pk])

    response = client.get(url, {"to_stage": Stage.REJECTED}, HTTP_HX_REQUEST="true")

    assert response.status_code == 302
    assert response.url.startswith(f"{reverse('login')}?next=")


def test_crafted_htmx_move_out_of_hired_is_refused(logged_in_client):
    application = ApplicationFactory(stage=Stage.HIRED)

    for to_stage in [Stage.OFFER, Stage.REJECTED, Stage.WITHDRAWN, Stage.APPLIED]:
        response = logged_in_client.post(
            reverse("applications:move", args=[application.pk]),
            {"to_stage": to_stage, "reason": "Crafted"},
            HTTP_HX_REQUEST="true",
        )
        assert "can&#x27;t be moved from Hired" in response.content.decode()

    application.refresh_from_db()
    assert application.stage == Stage.HIRED
    assert application.stage_changes.count() == 0


def test_hiring_through_the_board_leaves_the_job_open(logged_in_client):
    job = JobOpeningFactory(status=JobOpening.Status.OPEN)
    application = ApplicationFactory(job=job, stage=Stage.OFFER)

    logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"to_stage": Stage.HIRED},
        HTTP_HX_REQUEST="true",
    )

    application.refresh_from_db()
    job.refresh_from_db()
    assert application.stage == Stage.HIRED
    assert job.status == JobOpening.Status.OPEN
    assert job.closed_at is None
