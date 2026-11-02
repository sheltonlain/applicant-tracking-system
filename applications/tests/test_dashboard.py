import re

from django.urls import reverse

from applications.models import Application
from applications.services import jobs_needing_attention, open_job_summaries
from applications.tests.factories import ApplicationFactory
from jobs.models import JobOpening
from jobs.tests.factories import JobOpeningFactory

Stage = Application.Stage


def test_each_open_job_gets_per_stage_counts_and_hired_closed_totals(db):
    job = JobOpeningFactory(title="Data Analyst")
    for stage in [Stage.APPLIED, Stage.APPLIED, Stage.INTERVIEW, Stage.OFFER, Stage.HIRED]:
        ApplicationFactory(job=job, stage=stage)
    ApplicationFactory(job=job, stage=Stage.REJECTED)
    ApplicationFactory(job=job, stage=Stage.WITHDRAWN)
    empty_job = JobOpeningFactory(title="Designer")
    # Another job's applications and a closed job must not leak into these cards.
    other_job = ApplicationFactory(stage=Stage.APPLIED).job
    closed_job = JobOpeningFactory(title="Closed Role", status=JobOpening.Status.CLOSED)
    ApplicationFactory(job=closed_job, stage=Stage.SCREENING)

    summaries = {s["job"]: s for s in open_job_summaries()}

    assert set(summaries) == {job, empty_job, other_job}  # open jobs only
    data_analyst = summaries[job]
    assert [(c["key"], c["count"]) for c in data_analyst["stage_counts"]] == [
        ("applied", 2),
        ("screening", 0),
        ("interview", 1),
        ("final_review", 0),
        ("offer", 1),
    ]
    assert data_analyst["hired"] == 1
    assert data_analyst["closed"] == 2  # Rejected + Withdrawn
    assert [c["count"] for c in summaries[empty_job]["stage_counts"]] == [0, 0, 0, 0, 0]
    assert summaries[empty_job]["hired"] == 0
    assert summaries[empty_job]["closed"] == 0


def test_needs_attention_lists_exactly_closed_jobs_with_an_active_application(db):
    closed = JobOpening.Status.CLOSED
    # Closed with active applications: listed, with how many are still active.
    unfinished = JobOpeningFactory(title="Unfinished", status=closed)
    ApplicationFactory(job=unfinished, stage=Stage.OFFER)
    ApplicationFactory(job=unfinished, stage=Stage.APPLIED)
    ApplicationFactory(job=unfinished, stage=Stage.HIRED)
    one_left = JobOpeningFactory(title="One left", status=closed)
    ApplicationFactory(job=one_left, stage=Stage.SCREENING)
    # Closed, but every application is Hired, Rejected, or Withdrawn: not listed.
    finished = JobOpeningFactory(title="Finished", status=closed)
    for stage in [Stage.HIRED, Stage.REJECTED, Stage.WITHDRAWN]:
        ApplicationFactory(job=finished, stage=stage)
    # Closed with no applications at all: not listed.
    JobOpeningFactory(title="Empty", status=closed)
    # Open with active applications: not listed (it has a normal dashboard card).
    open_job = JobOpeningFactory(title="Open")
    ApplicationFactory(job=open_job, stage=Stage.INTERVIEW)

    attention = {item["job"].title: item["active"] for item in jobs_needing_attention()}

    assert attention == {"Unfinished": 2, "One left": 1}


def card_html(page, job):
    match = re.search(rf'<a [^>]*id="job-card-{job.pk}"[^>]*>.*?</a>\s*\n', page, re.S)
    assert match, f"no dashboard card for {job}"
    return match.group(0)


def test_dashboard_page_shows_a_card_per_open_job_linking_to_its_board(logged_in_client):
    job = JobOpeningFactory(title="Data Analyst", department="Analytics", location="Austin")
    ApplicationFactory(job=job, stage=Stage.SCREENING)
    ApplicationFactory(job=job, stage=Stage.SCREENING)
    ApplicationFactory(job=job, stage=Stage.HIRED)
    ApplicationFactory(job=job, stage=Stage.WITHDRAWN)
    closed_job = JobOpeningFactory(title="Old Role", status=JobOpening.Status.CLOSED)

    page = logged_in_client.get(reverse("applications:dashboard")).content.decode()

    card = card_html(page, job)
    assert f'href="{reverse("applications:board", args=[job.pk])}"' in card
    assert "Data Analyst" in card and "Analytics · Austin" in card
    assert 'data-stage="screening" data-count="2"' in card
    assert 'data-stage="applied" data-count="0"' in card
    assert 'data-total="hired" data-count="1"' in card
    assert 'data-total="closed" data-count="1"' in card
    assert f'id="job-card-{closed_job.pk}"' not in page


def test_dashboard_lists_needs_attention_jobs_with_a_link_to_their_board(logged_in_client):
    unfinished = JobOpeningFactory(title="Unfinished Role", status=JobOpening.Status.CLOSED)
    ApplicationFactory(job=unfinished, stage=Stage.OFFER)
    finished = JobOpeningFactory(title="Finished Role", status=JobOpening.Status.CLOSED)
    ApplicationFactory(job=finished, stage=Stage.HIRED)

    page = logged_in_client.get(reverse("applications:dashboard")).content.decode()

    attention = page[page.index('id="needs-attention"') :]
    assert "Unfinished Role" in attention and "1 active" in attention
    assert reverse("applications:board", args=[unfinished.pk]) in attention
    assert "Finished Role" not in page


def test_dashboard_with_nothing_to_show_says_so(logged_in_client):
    page = logged_in_client.get(reverse("applications:dashboard")).content.decode()

    assert "No open jobs." in page
    assert "Nothing needs attention" in page


def test_job_detail_lazy_loads_the_warning_only_for_closed_jobs(logged_in_client):
    closed_job = JobOpeningFactory(status=JobOpening.Status.CLOSED)
    open_job = JobOpeningFactory()
    warning_url = reverse("applications:job_warning", args=[closed_job.pk])

    closed_page = logged_in_client.get(closed_job.get_absolute_url()).content.decode()
    open_page = logged_in_client.get(open_job.get_absolute_url()).content.decode()

    assert f'hx-get="{warning_url}"' in closed_page and 'hx-trigger="load"' in closed_page
    assert reverse("applications:job_warning", args=[open_job.pk]) not in open_page


def test_job_warning_shows_active_count_and_board_link_while_unfinished(logged_in_client):
    job = JobOpeningFactory(status=JobOpening.Status.CLOSED)
    ApplicationFactory(job=job, stage=Stage.APPLIED)
    ApplicationFactory(job=job, stage=Stage.FINAL_REVIEW)
    ApplicationFactory(job=job, stage=Stage.REJECTED)
    url = reverse("applications:job_warning", args=[job.pk])

    html = logged_in_client.get(url, HTTP_HX_REQUEST="true").content.decode()

    assert 'id="closed-job-warning"' in html
    assert "2 active applications" in html
    assert reverse("applications:board", args=[job.pk]) in html


def test_job_warning_is_empty_when_nothing_is_left_or_the_job_is_open(logged_in_client):
    finished = JobOpeningFactory(status=JobOpening.Status.CLOSED)
    ApplicationFactory(job=finished, stage=Stage.HIRED)
    open_job = JobOpeningFactory()
    ApplicationFactory(job=open_job, stage=Stage.INTERVIEW)

    for job in [finished, open_job]:
        url = reverse("applications:job_warning", args=[job.pk])
        html = logged_in_client.get(url, HTTP_HX_REQUEST="true").content.decode()
        assert 'id="closed-job-warning"' not in html


def test_job_warning_direct_visit_redirects_to_the_job_page(logged_in_client):
    job = JobOpeningFactory(status=JobOpening.Status.CLOSED)

    response = logged_in_client.get(reverse("applications:job_warning", args=[job.pk]))

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()


def test_dashboard_and_job_warning_require_login(client, db):
    job = JobOpeningFactory(status=JobOpening.Status.CLOSED)
    urls = [
        reverse("applications:dashboard"),
        reverse("applications:job_warning", args=[job.pk]),
    ]

    for url in urls:
        response = client.get(url, HTTP_HX_REQUEST="true")
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"
