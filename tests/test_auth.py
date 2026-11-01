import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from conftest import UserFactory

User = get_user_model()


@pytest.mark.parametrize(
    "url_name", ["login", "password_reset", "password_reset_done", "password_reset_complete"]
)
def test_login_and_password_reset_pages_are_public(client, db, url_name):
    response = client.get(reverse(url_name))
    assert response.status_code == 200


@pytest.mark.parametrize("url_name", ["password_change", "password_change_done"])
def test_password_change_pages_require_login(client, db, url_name):
    response = client.get(reverse(url_name))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


def test_login_page_uses_project_template(client, db):
    response = client.get(reverse("login"))
    assert "registration/auth_card.html" in [t.name for t in response.templates]
    assert "Forgot your password?" in response.content.decode()


def test_staff_can_log_in_with_username_and_password(client, staff_user, staff_password):
    response = client.post(
        reverse("login"), {"username": staff_user.username, "password": staff_password}
    )
    assert response.status_code == 302
    assert response.url == reverse("applications:dashboard")
    assert client.get(reverse("applications:dashboard")).status_code == 200


def test_wrong_password_shows_error(client, staff_user):
    response = client.post(reverse("login"), {"username": staff_user.username, "password": "nope"})
    assert response.status_code == 200
    assert "alert-error" in response.content.decode()


def test_inactive_user_cannot_log_in(client, db, staff_password):
    user = UserFactory(is_active=False)
    response = client.post(
        reverse("login"), {"username": user.username, "password": staff_password}
    )
    assert response.status_code == 200  # the form is shown again with an error
    assert "_auth_user_id" not in client.session


def test_logout_ends_the_session(logged_in_client):
    response = logged_in_client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")
    assert logged_in_client.get(reverse("applications:dashboard")).status_code == 302


def test_logged_in_user_can_change_password(logged_in_client, staff_user, staff_password):
    new_password = "another-Str0ng-password"
    response = logged_in_client.post(
        reverse("password_change"),
        {
            "old_password": staff_password,
            "new_password1": new_password,
            "new_password2": new_password,
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("password_change_done")
    staff_user.refresh_from_db()
    assert staff_user.check_password(new_password)


def test_navbar_shows_full_name_when_set(client, db):
    user = UserFactory(first_name="Maria", last_name="Lopez")
    client.force_login(user)
    response = client.get(reverse("applications:dashboard"))
    assert "Maria Lopez" in response.content.decode()


def test_admin_can_create_staff_account_and_deactivated_account_cannot_log_in(client, db):
    admin = UserFactory(is_staff=True, is_superuser=True)
    client.force_login(admin)

    response = client.post(
        reverse("admin:auth_user_add"),
        {
            "username": "newhire",
            "usable_password": "true",
            "password1": "a-Str0ng-password",
            "password2": "a-Str0ng-password",
        },
    )
    assert response.status_code == 302
    new_hire = User.objects.get(username="newhire")
    assert new_hire.is_active

    response = client.get(reverse("admin:auth_user_change", args=[new_hire.pk]))
    assert response.status_code == 200

    new_hire.is_active = False
    new_hire.save()
    assert not client.login(username="newhire", password="a-Str0ng-password")


def test_password_reset_flow_lets_staff_log_in_with_new_password(client, staff_user):
    # Request a reset for the staff member's email address.
    response = client.post(reverse("password_reset"), {"email": staff_user.email})
    assert response.status_code == 302
    assert response.url == reverse("password_reset_done")

    # Exactly one email is sent, to that staff member, containing a reset link.
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == [staff_user.email]
    link = re.search(r"https?://[^/\s]+(/accounts/reset/\S+/)", email.body).group(1)

    # Following the link leads to a "set new password" form.
    set_password_page = client.get(link, follow=True)
    assert set_password_page.status_code == 200
    set_password_url = set_password_page.redirect_chain[-1][0]

    # Setting a new password completes the flow.
    new_password = "a-brand-new-Passw0rd"
    response = client.post(
        set_password_url, {"new_password1": new_password, "new_password2": new_password}
    )
    assert response.status_code == 302
    assert response.url == reverse("password_reset_complete")

    # The staff member can now log in with the new password through the login page.
    response = client.post(
        reverse("login"), {"username": staff_user.username, "password": new_password}
    )
    assert response.status_code == 302
    assert response.url == reverse("applications:dashboard")
