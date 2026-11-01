from django.urls import reverse

from candidates.models import Candidate
from candidates.tests.factories import CandidateFactory
from conftest import UserFactory


def test_admin_refuses_duplicate_email_in_different_case_with_form_error(client, db):
    client.force_login(UserFactory(is_staff=True, is_superuser=True))
    CandidateFactory(email="jane@example.com")

    response = client.post(
        reverse("admin:candidates_candidate_add"),
        {"first_name": "Janet", "last_name": "Roe", "email": "JANE@example.com"},
    )

    assert response.status_code == 200
    assert response.context["adminform"].form.errors["email"]
    assert Candidate.objects.count() == 1
