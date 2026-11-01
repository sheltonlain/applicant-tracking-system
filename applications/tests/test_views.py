from django.urls import reverse


def test_home_requires_login_and_shows_username_in_navbar(client, staff_user):
    home = reverse("applications:dashboard")

    anonymous = client.get(home)
    assert anonymous.status_code == 302
    assert anonymous.url == f"{reverse('login')}?next={home}"

    client.force_login(staff_user)
    logged_in = client.get(home)
    assert logged_in.status_code == 200
    assert staff_user.username in logged_in.content.decode()
