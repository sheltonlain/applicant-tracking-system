"""Shared pytest fixtures for the whole project."""

import factory
import pytest
from django.contrib.auth import get_user_model

STAFF_PASSWORD = "correct-horse-battery-staple"


class UserFactory(factory.django.DjangoModelFactory):
    """A regular staff member (not an admin)."""

    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"staff{n}")
    email = factory.LazyAttribute(lambda u: f"{u.username}@example.com")
    password = factory.django.Password(STAFF_PASSWORD)


@pytest.fixture
def staff_password():
    return STAFF_PASSWORD


@pytest.fixture
def staff_user(db):
    return UserFactory()


@pytest.fixture
def logged_in_client(client, staff_user):
    client.force_login(staff_user)
    return client


@pytest.fixture(autouse=True)
def temp_media_root(settings, tmp_path):
    """Every test stores uploads in its own temporary folder, so no files are left behind."""
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT
