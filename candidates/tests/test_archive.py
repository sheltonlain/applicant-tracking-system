import html
import re

import pytest
from django.urls import reverse

from candidates.models import Candidate
from candidates.services import CandidateStatusError, unarchive_candidate
from candidates.tests.factories import CandidateFactory
from conftest import UserFactory


def unarchive_url(candidate):
    return reverse("candidates:unarchive", args=[candidate.pk])


# --- Unarchive -------------------------------------------------------------------------------


def test_unarchive_always_succeeds(db):
    candidate = CandidateFactory(archived=True)

    unarchive_candidate(candidate)

    candidate.refresh_from_db()
    assert candidate.archived is False


def test_unarchiving_a_candidate_who_is_not_archived_is_refused(db):
    candidate = CandidateFactory()

    with pytest.raises(CandidateStatusError, match="not archived"):
        unarchive_candidate(candidate)


def test_unarchive_button_unarchives_and_returns_to_the_candidate_page(logged_in_client):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe", archived=True)

    response = logged_in_client.post(unarchive_url(candidate), follow=True)

    candidate.refresh_from_db()
    assert candidate.archived is False
    assert response.redirect_chain[-1][0] == candidate.get_absolute_url()
    assert "Jane Doe unarchived." in response.content.decode()


def test_unarchiving_twice_shows_a_friendly_note(logged_in_client):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe")

    response = logged_in_client.post(unarchive_url(candidate), follow=True)

    assert response.status_code == 200
    assert "Jane Doe is not archived." in response.content.decode()


def test_unarchive_only_accepts_post(logged_in_client):
    candidate = CandidateFactory(archived=True)

    assert logged_in_client.get(unarchive_url(candidate)).status_code == 405
    candidate.refresh_from_db()
    assert candidate.archived is True


def test_unarchive_requires_login(client, db):
    candidate = CandidateFactory(archived=True)

    response = client.post(unarchive_url(candidate))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
    candidate.refresh_from_db()
    assert candidate.archived is True


# --- Candidate page --------------------------------------------------------------------------


def test_archived_candidate_page_says_so_and_offers_unarchive_in_a_dialog(logged_in_client):
    candidate = CandidateFactory(archived=True)

    page = logged_in_client.get(candidate.get_absolute_url()).content.decode()

    assert "This candidate is archived" in page
    assert '<dialog id="archive-dialog"' in page
    assert f'action="{unarchive_url(candidate)}"' in page


# --- List ------------------------------------------------------------------------------------


@pytest.mark.parametrize("status", ["active", "archived", "all"])
def test_status_dropdown_shows_the_status_from_the_url(logged_in_client, status):
    page = logged_in_client.get(reverse("candidates:list"), {"status": status}).content.decode()

    selected = re.findall(r'<option value="(\w+)" selected>', page)
    assert selected == [status]


def test_status_dropdown_defaults_to_active(logged_in_client):
    page = logged_in_client.get(reverse("candidates:list")).content.decode()

    assert re.findall(r'<option value="(\w+)" selected>', page) == ["active"]


def test_archived_rows_are_marked_with_a_badge(logged_in_client):
    CandidateFactory(first_name="Jane", last_name="Archived", archived=True)
    CandidateFactory(first_name="Bob", last_name="Current")

    page = logged_in_client.get(reverse("candidates:list"), {"status": "all"}).content.decode()

    assert page.count("Archived</span>") == 1  # Jane's badge only


def test_search_box_and_status_send_each_other_along(logged_in_client):
    page = logged_in_client.get(reverse("candidates:list")).content.decode()

    assert page.count('hx-include="closest form"') == 2


def test_pagination_links_keep_the_status_and_the_search(logged_in_client):
    CandidateFactory.create_batch(20, first_name="Jane")
    CandidateFactory.create_batch(30, first_name="Jane", archived=True)
    url = reverse("candidates:list")

    page_one = logged_in_client.get(url, {"q": "jane", "status": "archived"}).content.decode()
    next_href = html.unescape(re.search(r'href="([^"]*page=2[^"]*)"', page_one).group(1))
    page_two = logged_in_client.get(url + next_href)

    candidates = list(page_two.context["page_obj"])
    assert len(candidates) == 5  # the last 5 of 30 archived Janes, not 25 of 50 Janes
    assert all(candidate.archived for candidate in candidates)


def test_htmx_status_request_gets_only_the_results(logged_in_client):
    CandidateFactory(first_name="Jane", last_name="Archived", archived=True)

    response = logged_in_client.get(
        reverse("candidates:list"), {"status": "archived"}, headers={"HX-Request": "true"}
    )

    partial = response.content.decode()
    assert "<html" not in partial
    assert "Jane Archived" in partial


# --- Admin -----------------------------------------------------------------------------------


def test_admin_cannot_change_the_archived_flag(client, db):
    client.force_login(UserFactory(is_staff=True, is_superuser=True))
    candidate = CandidateFactory(first_name="Jane", last_name="Doe", email="jane@example.com")

    client.post(
        reverse("admin:candidates_candidate_change", args=[candidate.pk]),
        {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "archived": "on",
        },
    )

    candidate.refresh_from_db()
    assert candidate.archived is False


def test_default_listing_method_leaves_out_archived_candidates(db):
    current = CandidateFactory()
    CandidateFactory(archived=True)

    assert list(Candidate.objects.not_archived()) == [current]
    assert Candidate.objects.count() == 2
