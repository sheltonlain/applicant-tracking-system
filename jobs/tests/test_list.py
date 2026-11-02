import html
import re
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from jobs.models import JobOpening
from jobs.tests.factories import JobOpeningFactory


def test_status_filter_combines_with_title_search_and_defaults_to_open(logged_in_client):
    open_analyst = JobOpeningFactory(title="Data Analyst", status=JobOpening.Status.OPEN)
    closed_analyst = JobOpeningFactory(
        title="Senior Data Analyst", status=JobOpening.Status.CLOSED, closed_at=timezone.now()
    )
    JobOpeningFactory(title="Designer", status=JobOpening.Status.OPEN)
    JobOpeningFactory(title="Recruiter", status=JobOpening.Status.CLOSED, closed_at=timezone.now())

    def titles(**params):
        response = logged_in_client.get(reverse("jobs:list"), {"q": "analyst", **params})
        return {job.title for job in response.context["page_obj"]}

    assert titles() == {open_analyst.title}  # no status chosen: Open
    assert titles(status="open") == {open_analyst.title}
    assert titles(status="closed") == {closed_analyst.title}
    assert titles(status="all") == {open_analyst.title, closed_analyst.title}
    assert titles(status="banana") == {open_analyst.title}  # a hand-edited link falls back to Open


def test_search_matches_title_department_or_location_ignoring_case(logged_in_client):
    finance = JobOpeningFactory(title="Data Analyst", department="Finance", location="Remote")
    marketing = JobOpeningFactory(title="Data Analyst", department="Marketing", location="Amarillo")
    JobOpeningFactory(title="Designer", department="Product", location="Dallas")

    def search(q):
        response = logged_in_client.get(reverse("jobs:list"), {"q": q})
        return set(response.context["page_obj"])

    assert search("FINANCE") == {finance}  # department, different case
    assert search("amarillo") == {marketing}  # location
    assert search("analyst") == {finance, marketing}  # title
    assert search("analyst remote") == {finance}  # words can match different fields


def test_list_is_newest_first(logged_in_client):
    older = JobOpeningFactory(title="Older")
    newer = JobOpeningFactory(title="Newer")
    JobOpening.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(days=2))

    response = logged_in_client.get(reverse("jobs:list"))

    assert list(response.context["page_obj"]) == [newer, older]


def test_list_is_paginated_at_25(logged_in_client):
    JobOpeningFactory.create_batch(26)
    url = reverse("jobs:list")

    assert len(logged_in_client.get(url).context["page_obj"]) == 25
    assert len(logged_in_client.get(url, {"page": 2}).context["page_obj"]) == 1


def test_htmx_request_gets_only_results_partial_and_normal_request_gets_full_page(
    logged_in_client,
):
    JobOpeningFactory(title="Data Analyst")
    url = reverse("jobs:list")

    full = logged_in_client.get(url, {"q": "analyst"}).content.decode()
    partial = logged_in_client.get(url, {"q": "analyst"}, headers={"HX-Request": "true"})
    partial = partial.content.decode()

    assert "<html" in full
    assert 'id="job-results"' in full
    assert "<html" not in partial
    assert 'id="job-results"' in partial
    assert "Data Analyst" in partial


def test_back_button_history_restore_gets_the_full_page(logged_in_client):
    headers = {"HX-Request": "true", "HX-History-Restore-Request": "true"}

    response = logged_in_client.get(reverse("jobs:list"), {"status": "closed"}, headers=headers)

    assert "<html" in response.content.decode()


def test_search_and_status_controls_update_the_url_and_send_each_other(logged_in_client):
    page = logged_in_client.get(reverse("jobs:list")).content.decode()

    # Both controls push the URL and include the whole form, so neither resets the other.
    assert page.count('hx-push-url="true"') == 2
    assert page.count('hx-include="closest form"') == 2


def test_loading_a_filtered_url_directly_shows_the_same_choices_and_results(logged_in_client):
    JobOpeningFactory(
        title="Data Analyst", status=JobOpening.Status.CLOSED, closed_at=timezone.now()
    )
    JobOpeningFactory(title="Data Engineer", status=JobOpening.Status.OPEN)

    page = logged_in_client.get(reverse("jobs:list") + "?q=data&status=closed").content.decode()

    assert 'value="data"' in page  # search box is pre-filled
    assert '<option value="closed" selected>' in page
    assert "Data Analyst" in page
    assert "Data Engineer" not in page


def test_pagination_links_preserve_the_search_and_status(logged_in_client):
    JobOpeningFactory.create_batch(
        30, title="Analyst", status=JobOpening.Status.CLOSED, closed_at=timezone.now()
    )
    JobOpeningFactory.create_batch(5, title="Analyst", status=JobOpening.Status.OPEN)
    url = reverse("jobs:list")

    page_one = logged_in_client.get(url, {"q": "analyst", "status": "closed"}).content.decode()
    next_href = html.unescape(re.search(r'href="([^"]*page=2[^"]*)"', page_one).group(1))
    page_two = logged_in_client.get(url + next_href)

    jobs = list(page_two.context["page_obj"])
    assert len(jobs) == 5  # the last 5 of 30 closed analysts, not 10 of 35 analysts
    assert all(job.status == JobOpening.Status.CLOSED for job in jobs)


def test_search_with_no_matches_shows_a_message(logged_in_client):
    response = logged_in_client.get(reverse("jobs:list"), {"q": "nobody"})

    assert "No job openings found." in response.content.decode()
