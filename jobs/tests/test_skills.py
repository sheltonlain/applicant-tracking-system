import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.urls import reverse

from jobs.forms import SkillForm
from jobs.models import JobOpening, Skill
from jobs.services import SkillInUseError, delete_skill
from jobs.tests.factories import JobOpeningFactory, SkillFactory


def test_skill_name_differing_only_in_case_is_refused_on_create_and_rename(db):
    SkillFactory(name="Python")
    sql = SkillFactory(name="SQL")

    create = SkillForm(data={"name": "python"})
    rename = SkillForm(data={"name": "PYTHON"}, instance=sql)

    for form in [create, rename]:
        assert not form.is_valid()
        assert form.errors.get("name") == ["A skill named “Python” already exists."]
    assert sorted(Skill.objects.values_list("name", flat=True)) == ["Python", "SQL"]


def test_deleting_a_skill_in_use_is_blocked_but_an_unused_skill_is_deleted(db):
    python = SkillFactory(name="Python")
    unused = SkillFactory(name="COBOL")
    for title in ["Data Analyst", "Junior Developer"]:
        JobOpeningFactory(title=title).skills.add(python)

    with pytest.raises(SkillInUseError) as blocked:
        delete_skill(python)

    assert str(blocked.value) == (
        "“Python” is used by 2 job openings, so it can't be deleted. "
        "Remove it from those jobs first."
    )
    assert python.jobs.count() == 2  # the skill and both jobs' links to it are untouched

    delete_skill(unused)

    assert list(Skill.objects.values_list("name", flat=True)) == ["Python"]


def is_ticked(html, skill):
    return f'name="skills" value="{skill.pk}" checked' in html


def test_add_button_creates_the_skill_and_returns_the_list_with_it_and_earlier_ticks_ticked(
    logged_in_client,
):
    sql = SkillFactory(name="SQL")
    python = SkillFactory(name="Python")

    # "+ Add" sends the new name and the boxes currently ticked on the job form (only SQL).
    response = logged_in_client.post(
        reverse("jobs:skill_add"),
        {"new_skill": "Tableau", "skills": [sql.pk]},
        headers={"HX-Request": "true"},
    )

    assert Skill.objects.filter(name="Tableau").exists()
    tableau = Skill.objects.get(name="Tableau")
    html = response.content.decode()
    assert "<html" not in html  # only the skills area, not a whole page
    assert is_ticked(html, tableau)
    assert is_ticked(html, sql)
    assert not is_ticked(html, python)
    assert f'value="{python.pk}"' in html  # still listed, just not ticked


def test_add_button_refuses_a_name_differing_only_in_case_inline_and_keeps_ticks(
    logged_in_client,
):
    python = SkillFactory(name="Python")
    sql = SkillFactory(name="SQL")

    response = logged_in_client.post(
        reverse("jobs:skill_add"),
        {"new_skill": "python", "skills": [sql.pk]},
        headers={"HX-Request": "true"},
    )

    html = response.content.decode()
    assert "A skill named “Python” already exists." in html
    assert 'value="python"' in html  # the typed name stays in the box to fix
    assert is_ticked(html, sql)
    assert not is_ticked(html, python)
    assert Skill.objects.count() == 2


def test_add_button_refuses_get_requests(logged_in_client):
    assert logged_in_client.get(reverse("jobs:skill_add")).status_code == 405


VALID_JOB = {
    "title": "Data Analyst",
    "department": "Finance",
    "location": "Remote",
    "employment_type": JobOpening.EmploymentType.FULL_TIME,
    "description": "Analyze data.",
}


def test_job_form_saves_ticked_skills_on_create_and_edit(logged_in_client):
    python, sql, excel = (SkillFactory(name=n) for n in ["Python", "SQL", "Excel"])

    logged_in_client.post(reverse("jobs:create"), {**VALID_JOB, "skills": [python.pk, sql.pk]})
    job = JobOpening.objects.get()
    assert set(job.skills.all()) == {python, sql}

    logged_in_client.post(reverse("jobs:edit", args=[job.pk]), {**VALID_JOB, "skills": [excel.pk]})
    assert set(job.skills.all()) == {excel}


def test_edit_form_shows_the_jobs_current_skills_ticked_with_the_add_box(logged_in_client):
    python, sql = SkillFactory(name="Python"), SkillFactory(name="SQL")
    job = JobOpeningFactory()
    job.skills.add(python)

    html = logged_in_client.get(reverse("jobs:edit", args=[job.pk])).content.decode()

    assert is_ticked(html, python)
    assert not is_ticked(html, sql)
    assert f'hx-post="{reverse("jobs:skill_add")}"' in html


def test_renaming_a_skill_changes_it_on_every_job_that_uses_it(logged_in_client):
    skill = SkillFactory(name="Pyhton")
    jobs = [JobOpeningFactory(), JobOpeningFactory()]
    for job in jobs:
        job.skills.add(skill)

    response = logged_in_client.post(
        reverse("jobs:skill_edit", args=[skill.pk]), {"name": "Python"}, follow=True
    )

    assert "Skill renamed." in response.content.decode()
    for job in jobs:
        detail = logged_in_client.get(reverse("jobs:detail", args=[job.pk])).content.decode()
        assert "Python" in detail
        assert "Pyhton" not in detail


def test_renaming_a_skill_to_its_own_name_in_different_case_is_allowed(logged_in_client):
    skill = SkillFactory(name="python")

    logged_in_client.post(reverse("jobs:skill_edit", args=[skill.pk]), {"name": "Python"})

    skill.refresh_from_db()
    assert skill.name == "Python"


def test_job_detail_shows_its_skills(logged_in_client):
    job = JobOpeningFactory()
    job.skills.add(SkillFactory(name="Python"), SkillFactory(name="SQL"))
    SkillFactory(name="COBOL")  # not on this job

    html = logged_in_client.get(reverse("jobs:detail", args=[job.pk])).content.decode()

    assert '<span class="badge badge-outline">Python</span>' in html
    assert '<span class="badge badge-outline">SQL</span>' in html
    assert "COBOL" not in html


def test_skills_page_lists_skills_with_job_counts_and_adds_new_ones(logged_in_client):
    python = SkillFactory(name="Python")
    JobOpeningFactory().skills.add(python)
    SkillFactory(name="COBOL")

    html = logged_in_client.get(reverse("jobs:skill_list")).content.decode()
    assert html.index("COBOL") < html.index("Python")  # A to Z
    assert "1 job ▾<" in html
    assert "0 jobs" in html

    added = logged_in_client.post(reverse("jobs:skill_list"), {"name": "Tableau"}, follow=True)
    assert "Skill “Tableau” added." in added.content.decode()
    refused = logged_in_client.post(reverse("jobs:skill_list"), {"name": "PYTHON"})
    assert "A skill named “Python” already exists." in refused.content.decode()
    assert Skill.objects.count() == 3


def test_skills_page_used_by_count_opens_a_list_linking_to_each_jobs_edit_page(
    logged_in_client,
):
    python = SkillFactory(name="Python")
    analyst = JobOpeningFactory(title="Data Analyst", department="Finance", location="Remote")
    developer = JobOpeningFactory(title="Junior Developer", department="IT", location="Dallas")
    other = JobOpeningFactory(title="Recruiter", department="HR", location="Austin")
    for job in [analyst, developer]:
        job.skills.add(python)
    SkillFactory(name="COBOL")  # used by no job: plain "0 jobs", no list

    html = logged_in_client.get(reverse("jobs:skill_list")).content.decode()

    for job in [analyst, developer]:
        assert f'<a href="{reverse("jobs:edit", args=[job.pk])}">{job}</a>' in html
    assert reverse("jobs:edit", args=[other.pk]) not in html
    assert html.count("<details") == 1  # only Python's count opens a list


def test_deleting_from_the_skills_page_shows_friendly_messages(logged_in_client):
    in_use, unused = SkillFactory(name="Python"), SkillFactory(name="COBOL")
    JobOpeningFactory().skills.add(in_use)

    blocked = logged_in_client.post(reverse("jobs:skill_delete", args=[in_use.pk]), follow=True)
    deleted = logged_in_client.post(reverse("jobs:skill_delete", args=[unused.pk]), follow=True)
    repeated = logged_in_client.post(reverse("jobs:skill_delete", args=[unused.pk]), follow=True)

    assert "“Python” is used by 1 job opening, so it can&#x27;t be deleted." in (
        blocked.content.decode()
    )
    assert "Skill “COBOL” deleted." in deleted.content.decode()
    assert "That skill was already deleted." in repeated.content.decode()
    assert repeated.status_code == 200
    assert list(Skill.objects.all()) == [in_use]


def test_skill_in_use_cannot_be_deleted_even_outside_the_app(db):
    skill = SkillFactory(name="Python")
    JobOpeningFactory().skills.add(skill)

    with pytest.raises(ProtectedError):
        skill.delete()  # e.g. the admin: the PROTECT link blocks it


def test_database_refuses_a_skill_name_differing_only_in_case(db):
    SkillFactory(name="Python")

    with pytest.raises(IntegrityError):
        Skill.objects.create(name="PYTHON")  # code that skips the form's check


def test_deleting_a_job_keeps_its_skills(db):
    skill = SkillFactory(name="Python")
    job = JobOpeningFactory()
    job.skills.add(skill)

    job.delete()

    assert Skill.objects.filter(pk=skill.pk).exists()


@pytest.mark.parametrize(
    ("name", "method", "needs_pk"),
    [
        ("jobs:skill_list", "get", False),
        ("jobs:skill_add", "post", False),
        ("jobs:skill_edit", "get", True),
        ("jobs:skill_delete", "post", True),
    ],
)
def test_skill_views_require_login(client, db, name, method, needs_pk):
    skill = SkillFactory()
    url = reverse(name, args=[skill.pk]) if needs_pk else reverse(name)

    data = {"name": "Hacked", "new_skill": "Hacked"} if method == "post" else None
    response = getattr(client, method)(url, data)

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={url}"
    assert list(Skill.objects.all()) == [skill]
