import pytest
from django.urls import reverse

from candidates.models import Candidate
from candidates.tests.factories import CandidateFactory


def test_create_candidate_stores_lowercase_email_and_redirects_to_detail(logged_in_client):
    response = logged_in_client.post(
        reverse("candidates:create"),
        {"first_name": "Jane", "last_name": "Doe", "email": "Jane@Example.com"},
    )

    candidate = Candidate.objects.get()
    assert candidate.email == "jane@example.com"
    assert response.status_code == 302
    assert response.url == reverse("candidates:detail", args=[candidate.pk])


def test_duplicate_email_in_different_case_is_refused_on_create_and_edit(logged_in_client):
    jane = CandidateFactory(email="jane@example.com")
    other = CandidateFactory(email="other@example.com")
    duplicate = {"first_name": "Janet", "last_name": "Roe", "email": "JANE@example.com"}

    create = logged_in_client.post(reverse("candidates:create"), duplicate)
    assert create.status_code == 200
    assert create.context["form"].errors["email"]
    assert Candidate.objects.count() == 2

    edit = logged_in_client.post(reverse("candidates:edit", args=[other.pk]), duplicate)
    assert edit.status_code == 200
    assert edit.context["form"].errors["email"]
    other.refresh_from_db()
    assert other.email == "other@example.com"
    jane.refresh_from_db()
    assert jane.first_name != "Janet"


@pytest.mark.parametrize("phone", ["+44 20 7946 0958", "(806) 555-0142 ext. 12", "555.0142"])
def test_phone_numbers_in_any_format_are_accepted(logged_in_client, phone):
    logged_in_client.post(
        reverse("candidates:create"),
        {"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com", "phone": phone},
    )

    assert Candidate.objects.get().phone == phone


def test_edit_saves_changes_and_redirects_to_detail(logged_in_client):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe", email="jane@example.com")

    response = logged_in_client.post(
        reverse("candidates:edit", args=[candidate.pk]),
        {"first_name": "Jane", "last_name": "Smith", "email": "Jane.Smith@Example.com"},
    )

    assert response.url == reverse("candidates:detail", args=[candidate.pk])
    candidate.refresh_from_db()
    assert candidate.last_name == "Smith"
    assert candidate.email == "jane.smith@example.com"


def test_edit_keeping_the_same_email_is_allowed(logged_in_client):
    candidate = CandidateFactory(email="jane@example.com")

    response = logged_in_client.post(
        reverse("candidates:edit", args=[candidate.pk]),
        {"first_name": "Jane", "last_name": "Doe", "email": "JANE@example.com"},
    )

    assert response.status_code == 302


def test_detail_shows_full_name_contact_details_and_notes(logged_in_client):
    candidate = CandidateFactory(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="+1 806 555 0142",
        url="https://linkedin.com/in/janedoe",
        notes="Strong Python background.",
    )

    content = logged_in_client.get(reverse("candidates:detail", args=[candidate.pk])).content
    page = content.decode()

    for text in [
        "Jane Doe",
        "jane@example.com",
        "+1 806 555 0142",
        "https://linkedin.com/in/janedoe",
        "Strong Python background.",
    ]:
        assert text in page


def test_unknown_candidate_returns_404(logged_in_client):
    assert logged_in_client.get(reverse("candidates:detail", args=[999])).status_code == 404


@pytest.mark.parametrize("name", ["candidates:create", "candidates:detail", "candidates:edit"])
def test_candidate_views_require_login(client, db, name):
    candidate = CandidateFactory()
    url = reverse(name) if name == "candidates:create" else reverse(name, args=[candidate.pk])

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={url}"


def test_detail_page_links_back_to_all_candidates(logged_in_client):
    candidate = CandidateFactory()

    page = logged_in_client.get(reverse("candidates:detail", args=[candidate.pk])).content.decode()

    assert f'href="{reverse("candidates:list")}"' in page
    assert "All candidates" in page
