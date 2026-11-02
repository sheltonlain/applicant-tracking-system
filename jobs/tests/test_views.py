import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from jobs.models import JobOpening
from jobs.tests.factories import JobOpeningFactory

VALID_JOB = {
    "title": "Data Analyst",
    "department": "Finance",
    "location": "Remote",
    "employment_type": JobOpening.EmploymentType.FULL_TIME,
    "description": "Analyze data.",
}


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


def test_create_job_starts_open_and_redirects_to_detail(logged_in_client):
    response = logged_in_client.post(reverse("jobs:create"), VALID_JOB)

    job = JobOpening.objects.get()
    assert job.status == JobOpening.Status.OPEN
    assert job.closed_at is None
    assert response.url == reverse("jobs:detail", args=[job.pk])


def test_two_jobs_with_the_same_title_can_be_created(logged_in_client):
    logged_in_client.post(reverse("jobs:create"), VALID_JOB)
    logged_in_client.post(reverse("jobs:create"), {**VALID_JOB, "department": "Marketing"})

    assert JobOpening.objects.filter(title="Data Analyst").count() == 2


def test_create_with_missing_fields_shows_errors_and_saves_nothing(logged_in_client):
    response = logged_in_client.post(reverse("jobs:create"), {"title": "Data Analyst"})

    assert response.status_code == 200
    errors = response.context["form"].errors
    assert {"department", "location", "employment_type", "description"} <= set(errors)
    assert not JobOpening.objects.exists()


def test_edit_saves_changes_but_cannot_change_status(logged_in_client):
    job = JobOpeningFactory(title="Data Analyst", status=JobOpening.Status.OPEN)

    response = logged_in_client.post(
        reverse("jobs:edit", args=[job.pk]),
        {**VALID_JOB, "title": "Senior Data Analyst", "status": JobOpening.Status.CLOSED},
    )

    assert response.url == reverse("jobs:detail", args=[job.pk])
    job.refresh_from_db()
    assert job.title == "Senior Data Analyst"
    assert job.status == JobOpening.Status.OPEN  # status changes only through Close / Reopen


def test_edit_form_shows_the_current_employment_type_selected(logged_in_client):
    job = JobOpeningFactory(employment_type=JobOpening.EmploymentType.CONTRACT)

    page = logged_in_client.get(reverse("jobs:edit", args=[job.pk])).content.decode()

    assert '<option value="contract" selected>Contract</option>' in page


def test_department_and_location_appear_next_to_the_title_in_list_and_detail(logged_in_client):
    job = JobOpeningFactory(title="Data Analyst", department="Finance", location="Amarillo")

    detail = logged_in_client.get(reverse("jobs:detail", args=[job.pk])).content.decode()
    listing = logged_in_client.get(reverse("jobs:list")).content.decode()

    assert "Finance · Amarillo" in detail
    for page in [detail, listing]:
        assert "Data Analyst" in page
        assert "Finance" in page
        assert "Amarillo" in page
    assert str(job) == "Data Analyst — Finance · Amarillo"


def test_open_job_shows_only_close_button_and_closed_job_shows_only_reopen(logged_in_client):
    open_job = JobOpeningFactory(status=JobOpening.Status.OPEN)
    closed_job = JobOpeningFactory(status=JobOpening.Status.CLOSED, closed_at=timezone.now())

    open_page = logged_in_client.get(reverse("jobs:detail", args=[open_job.pk])).content.decode()
    closed_page = logged_in_client.get(
        reverse("jobs:detail", args=[closed_job.pk])
    ).content.decode()

    assert reverse("jobs:close", args=[open_job.pk]) in open_page
    assert reverse("jobs:reopen", args=[open_job.pk]) not in open_page
    assert reverse("jobs:reopen", args=[closed_job.pk]) in closed_page
    assert reverse("jobs:close", args=[closed_job.pk]) not in closed_page


def test_close_and_reopen_buttons_toggle_the_job_with_success_messages(logged_in_client):
    job = JobOpeningFactory(status=JobOpening.Status.OPEN)

    close = logged_in_client.post(reverse("jobs:close", args=[job.pk]), follow=True)
    job.refresh_from_db()
    assert job.status == JobOpening.Status.CLOSED
    assert "Job closed. No new applications can be added." in close.content.decode()

    reopen = logged_in_client.post(reverse("jobs:reopen", args=[job.pk]), follow=True)
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN
    assert job.closed_at is None
    assert "Job reopened. New applications can be added." in reopen.content.decode()


@pytest.mark.parametrize(
    ("status", "action", "message"),
    [
        (JobOpening.Status.CLOSED, "jobs:close", "This job is already closed."),
        (JobOpening.Status.OPEN, "jobs:reopen", "This job is already open."),
    ],
)
def test_stale_close_or_reopen_shows_a_friendly_message_not_an_error(
    logged_in_client, status, action, message
):
    # e.g. the job was closed in another tab, then "Close job" is clicked on the old page.
    closed_at = timezone.now() if status == JobOpening.Status.CLOSED else None
    job = JobOpeningFactory(status=status, closed_at=closed_at)

    response = logged_in_client.post(reverse(action, args=[job.pk]))

    assert response.status_code == 302
    assert response.url == reverse("jobs:detail", args=[job.pk])
    assert messages_of(response) == [message]
    job.refresh_from_db()
    assert job.status == status
    assert job.closed_at == closed_at


@pytest.mark.parametrize("action", ["jobs:close", "jobs:reopen"])
def test_close_and_reopen_refuse_get_requests(logged_in_client, action):
    job = JobOpeningFactory()

    assert logged_in_client.get(reverse(action, args=[job.pk])).status_code == 405


def test_unknown_job_returns_404(logged_in_client):
    assert logged_in_client.get(reverse("jobs:detail", args=[999])).status_code == 404


@pytest.mark.parametrize(
    ("name", "method"),
    [
        ("jobs:list", "get"),
        ("jobs:create", "get"),
        ("jobs:detail", "get"),
        ("jobs:edit", "get"),
        ("jobs:close", "post"),
        ("jobs:reopen", "post"),
    ],
)
def test_job_views_require_login(client, db, name, method):
    job = JobOpeningFactory()
    no_pk = name in {"jobs:list", "jobs:create"}
    url = reverse(name) if no_pk else reverse(name, args=[job.pk])

    response = getattr(client, method)(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={url}"
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN


def test_new_job_page_links_back_to_the_job_list(logged_in_client):
    response = logged_in_client.post(reverse("jobs:create"), VALID_JOB, follow=True)

    assert f'href="{reverse("jobs:list")}"' in response.content.decode().split("<main", 1)[1]
