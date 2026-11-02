import re

from django.urls import reverse

from applications.models import Application
from applications.tests.factories import ApplicationFactory
from jobs.models import JobOpening
from jobs.tests.factories import JobOpeningFactory

Stage = Application.Stage

COLUMN = re.compile(r'<section id="column-(\w+)" data-count="(\d+)"[^>]*>(.*?)</section>', re.S)


def board_columns_in(html):
    """{column key: (count shown, column HTML)} for every column on the rendered board."""
    return {key: (int(count), body) for key, count, body in COLUMN.findall(html)}


def test_htmx_advance_returns_whole_board_with_both_columns_and_counts_updated(
    logged_in_client,
):
    job = JobOpeningFactory()
    moving = ApplicationFactory(
        job=job, stage=Stage.SCREENING, candidate__first_name="Ada", candidate__last_name="Moves"
    )
    ApplicationFactory(
        job=job, stage=Stage.SCREENING, candidate__first_name="Bo", candidate__last_name="Stays"
    )

    response = logged_in_client.post(
        reverse("applications:move", args=[moving.pk]),
        {"to_stage": Stage.INTERVIEW},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="board"' in html
    assert "<html" not in html  # just the board section, not a full page
    columns = board_columns_in(html)
    assert {key: count for key, (count, _) in columns.items()} == {
        "applied": 0,
        "screening": 1,
        "interview": 1,
        "final_review": 0,
        "offer": 0,
        "closed": 0,
    }
    assert "Ada Moves" in columns["interview"][1]
    assert "Ada Moves" not in columns["screening"][1]
    assert "Bo Stays" in columns["screening"][1]


def card_targets(column_html):
    """The to_stage values of every move button drawn in a column."""
    return re.findall(r'name="to_stage" value="(\w+)"', column_html)


def test_board_page_shows_every_column_and_only_allowed_buttons(logged_in_client, staff_user):
    job = JobOpeningFactory(title="Data Analyst", department="Analytics", location="Remote")
    ApplicationFactory(
        job=job,
        stage=Stage.APPLIED,
        candidate__first_name="Ann",
        candidate__last_name="Applied",
        source=Application.Source.REFERRAL,
        source_note="Referred by Maria",
    )
    ApplicationFactory(job=job, stage=Stage.INTERVIEW)
    ApplicationFactory(job=job, stage=Stage.OFFER)
    ApplicationFactory(job=job, stage=Stage.HIRED, candidate__last_name="Hiredson")
    ApplicationFactory(job=job, stage=Stage.REJECTED, candidate__last_name="Rejectson")
    ApplicationFactory(stage=Stage.APPLIED, candidate__last_name="OtherJob")  # another job

    response = logged_in_client.get(reverse("applications:board", args=[job.pk]))

    assert response.status_code == 200
    html = response.content.decode()
    assert "Data Analyst" in html and "Analytics · Remote" in html
    assert "OtherJob" not in html
    columns = board_columns_in(html)
    assert list(columns) == ["applied", "screening", "interview", "final_review", "offer", "closed"]
    applied = columns["applied"][1]
    assert "Ann Applied" in applied
    assert "Referral" in applied and "Referred by Maria" in applied
    # Applied: Advance only (no Back). Interview: Advance and Back.
    assert card_targets(applied) == [Stage.SCREENING]
    assert card_targets(columns["interview"][1]) == [Stage.FINAL_REVIEW, Stage.SCREENING]
    # Offer: Back is the only direct post; Mark Hired opens a confirmation dialog first.
    assert card_targets(columns["offer"][1]) == [Stage.FINAL_REVIEW]
    # Closed column holds Hired and Rejected, with their stage shown and no move buttons.
    closed_count, closed = columns["closed"]
    assert closed_count == 2
    assert "Hiredson" in closed and "Rejectson" in closed
    assert "Hired" in closed and "Rejected" in closed
    assert card_targets(closed) == []


def test_htmx_refused_move_redraws_board_with_a_friendly_note(logged_in_client):
    application = ApplicationFactory(stage=Stage.APPLIED, candidate__first_name="Ann")

    # A crafted request: skip from Applied straight to Offer.
    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"to_stage": Stage.OFFER},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="board"' in html
    assert 'role="alert"' in html and "can&#x27;t be moved from Applied to Offer" in html
    application.refresh_from_db()
    assert application.stage == Stage.APPLIED
    assert application.stage_changes.count() == 0


def test_non_htmx_move_redirects_to_the_board(logged_in_client):
    application = ApplicationFactory(stage=Stage.APPLIED)
    board_url = reverse("applications:board", args=[application.job.pk])

    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]), {"to_stage": Stage.SCREENING}
    )

    assert response.status_code == 302
    assert response.url == board_url
    application.refresh_from_db()
    assert application.stage == Stage.SCREENING


def test_non_htmx_refused_move_redirects_with_a_message(logged_in_client):
    application = ApplicationFactory(stage=Stage.HIRED)

    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"to_stage": Stage.OFFER},
        follow=True,
    )

    assert "can&#x27;t be moved from Hired to Offer" in response.content.decode()
    application.refresh_from_db()
    assert application.stage == Stage.HIRED


def test_moves_work_on_a_closed_jobs_board(logged_in_client):
    job = JobOpeningFactory(status=JobOpening.Status.CLOSED)
    application = ApplicationFactory(job=job, stage=Stage.INTERVIEW)

    board = logged_in_client.get(reverse("applications:board", args=[job.pk]))
    assert card_targets(board.content.decode()) == [Stage.FINAL_REVIEW, Stage.SCREENING]

    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"to_stage": Stage.FINAL_REVIEW},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == Stage.FINAL_REVIEW


def test_move_refuses_get(logged_in_client):
    application = ApplicationFactory(stage=Stage.APPLIED)

    response = logged_in_client.get(reverse("applications:move", args=[application.pk]))

    assert response.status_code == 405
    application.refresh_from_db()
    assert application.stage == Stage.APPLIED


def test_board_and_move_require_login(client, db):
    application = ApplicationFactory(stage=Stage.APPLIED)
    board_url = reverse("applications:board", args=[application.job.pk])
    move_url = reverse("applications:move", args=[application.pk])

    board = client.get(board_url)
    move = client.post(move_url, {"to_stage": Stage.SCREENING}, HTTP_HX_REQUEST="true")

    for response, url in [(board, board_url), (move, move_url)]:
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"
    application.refresh_from_db()
    assert application.stage == Stage.APPLIED


def test_job_detail_links_to_its_board(logged_in_client):
    job = JobOpeningFactory()

    response = logged_in_client.get(job.get_absolute_url())

    assert reverse("applications:board", args=[job.pk]) in response.content.decode()
