import pytest
from django.db import IntegrityError

from candidates.tests.factories import CandidateFactory


def test_full_name_joins_first_and_last_name(db):
    assert CandidateFactory(first_name="Jane", last_name="Doe").full_name == "Jane Doe"


def test_email_is_saved_lowercase_even_without_a_form(db):
    assert CandidateFactory(email="Jane@Example.COM").email == "jane@example.com"


def test_database_refuses_duplicate_email_in_different_case(db):
    CandidateFactory(email="jane@example.com")

    with pytest.raises(IntegrityError):
        CandidateFactory(email="JANE@example.com")
