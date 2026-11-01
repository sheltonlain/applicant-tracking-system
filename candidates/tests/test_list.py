import html
import re

from django.urls import reverse

from candidates.tests.factories import CandidateFactory


def test_list_is_sorted_by_last_name_then_first_name(logged_in_client):
    CandidateFactory(first_name="Zoe", last_name="Adams")
    CandidateFactory(first_name="Amy", last_name="Young")
    CandidateFactory(first_name="Ann", last_name="Adams")

    response = logged_in_client.get(reverse("candidates:list"))

    names = [candidate.full_name for candidate in response.context["page_obj"]]
    assert names == ["Ann Adams", "Zoe Adams", "Amy Young"]


def test_list_is_paginated_at_25(logged_in_client):
    CandidateFactory.create_batch(26)
    url = reverse("candidates:list")

    assert len(logged_in_client.get(url).context["page_obj"]) == 25
    assert len(logged_in_client.get(url, {"page": 2}).context["page_obj"]) == 1


def test_loading_a_search_url_directly_shows_the_search_and_its_results(logged_in_client):
    CandidateFactory(first_name="Jane", last_name="Doe", email="jane@example.com")
    CandidateFactory(first_name="Bob", last_name="Smith", email="bob@acme.com")

    page = logged_in_client.get(reverse("candidates:list") + "?q=jane").content.decode()

    assert 'value="jane"' in page  # search box is pre-filled
    assert "Jane Doe" in page
    assert "Bob Smith" not in page


def test_back_button_history_restore_gets_the_full_page(logged_in_client):
    headers = {"HX-Request": "true", "HX-History-Restore-Request": "true"}

    response = logged_in_client.get(reverse("candidates:list"), {"q": "jane"}, headers=headers)

    assert "<html" in response.content.decode()


def test_htmx_history_snapshots_are_disabled_so_back_always_refetches(logged_in_client):
    # Snapshots don't record typed text, so they can restore a search box that doesn't match the
    # results. With the cache off, Back asks the server, which renders both from the same query.
    page = logged_in_client.get(reverse("candidates:list")).content.decode()

    assert '"historyCacheSize": 0' in page


def test_search_with_no_matches_shows_a_message(logged_in_client):
    CandidateFactory(first_name="Jane")

    response = logged_in_client.get(reverse("candidates:list"), {"q": "nobody"})

    assert "No candidates found." in response.content.decode()


def test_candidate_list_requires_login(client, db):
    url = reverse("candidates:list")

    for headers in [{}, {"HX-Request": "true"}]:
        response = client.get(url, headers=headers)
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"


def test_search_matches_name_or_email_ignoring_case(logged_in_client):
    jane = CandidateFactory(first_name="Jane", last_name="Doe", email="jane@example.com")
    bob = CandidateFactory(first_name="Bob", last_name="Smith", email="bob@acme.com")
    CandidateFactory(first_name="Carol", last_name="Jones", email="carol@example.com")

    def search(q):
        response = logged_in_client.get(reverse("candidates:list"), {"q": q})
        return list(response.context["page_obj"])

    assert search("doe") == [jane]  # last name
    assert search("JANE") == [jane]  # first name, different case
    assert search("ACME.com") == [bob]  # email, different case
    assert search("jane doe") == [jane]  # full name across two fields
    assert search("doe jane") == [jane]  # word order doesn't matter


def test_htmx_request_gets_only_results_partial_and_normal_request_gets_full_page(
    logged_in_client,
):
    CandidateFactory(first_name="Jane", last_name="Doe", email="jane@example.com")
    url = reverse("candidates:list")

    full = logged_in_client.get(url, {"q": "jane"}).content.decode()
    partial = logged_in_client.get(url, {"q": "jane"}, headers={"HX-Request": "true"})
    partial = partial.content.decode()

    assert "<html" in full
    assert 'id="candidate-results"' in full
    assert "Jane Doe" in full

    assert "<html" not in partial
    assert 'id="candidate-results"' in partial
    assert "Jane Doe" in partial


def test_pagination_links_preserve_the_search_query(logged_in_client):
    CandidateFactory.create_batch(30, first_name="Jane")
    CandidateFactory.create_batch(5, first_name="Bob")
    url = reverse("candidates:list")

    page_one = logged_in_client.get(url, {"q": "jane"}).content.decode()
    next_href = html.unescape(re.search(r'href="([^"]*page=2[^"]*)"', page_one).group(1))
    page_two = logged_in_client.get(url + next_href)

    candidates = list(page_two.context["page_obj"])
    assert len(candidates) == 5  # the last 5 of 30 Janes, not 10 of 35 candidates
    assert all(candidate.first_name == "Jane" for candidate in candidates)
