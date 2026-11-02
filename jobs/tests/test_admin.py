from django.urls import reverse

from conftest import UserFactory
from jobs.models import Skill
from jobs.tests.factories import JobOpeningFactory, SkillFactory


def test_admin_shows_a_jobs_skills_and_refuses_to_delete_a_skill_in_use(client, db):
    client.force_login(UserFactory(is_staff=True, is_superuser=True))
    skill = SkillFactory(name="Python")
    job = JobOpeningFactory()
    job.skills.add(skill)

    change_page = client.get(reverse("admin:jobs_jobopening_change", args=[job.pk]))
    delete = client.post(reverse("admin:jobs_skill_delete", args=[skill.pk]), {"post": "yes"})

    assert "Python" in change_page.content.decode()
    assert "Cannot delete" in delete.content.decode()
    assert Skill.objects.filter(pk=skill.pk).exists()
