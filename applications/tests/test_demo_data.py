from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import CommandError, call_command
from django.db.models import Count

from applications.management.commands import load_demo_data as demo_command
from applications.models import Application, StageChange
from applications.services import create_application, jobs_needing_attention, move_application
from applications.stages import CLOSED_STAGES
from candidates.models import Candidate
from candidates.tests.factories import CandidateFactory
from jobs.models import JobOpening, Skill

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def debug_on(settings):
    # The command is development-only and refuses to run with DEBUG off.
    settings.DEBUG = True


def load(*args):
    out = StringIO()
    call_command("load_demo_data", *args, stdout=out)
    return out.getvalue()


def test_empty_database_gets_full_demo_dataset_and_prints_the_demo_login():
    output = load()

    stages_used = set(Application.objects.values_list("stage", flat=True))
    assert stages_used == set(Application.Stage.values)

    attention = [item["job"] for item in jobs_needing_attention()]
    assert len(attention) == 1
    assert attention[0].status == JobOpening.Status.CLOSED

    demo = get_user_model().objects.get(username="demo")
    assert "demo" in output
    password = output.split("Password:")[1].split()[0]
    assert demo.check_password(password)


def test_non_empty_database_is_refused_without_reset_and_nothing_changes():
    existing = CandidateFactory(email="real.person@example.com")

    with pytest.raises(CommandError, match="--reset"):
        load()

    assert list(Candidate.objects.all()) == [existing]
    assert not JobOpening.objects.exists()
    assert not Application.objects.exists()
    assert not get_user_model().objects.filter(username="demo").exists()


def test_reset_clears_existing_data_and_reloads_the_demo_dataset():
    load()
    first_counts = (
        Candidate.objects.count(),
        JobOpening.objects.count(),
        Skill.objects.count(),
        Application.objects.count(),
        StageChange.objects.count(),
    )
    CandidateFactory(email="extra.person@example.com")

    output = load("--reset")

    assert not Candidate.objects.filter(email="extra.person@example.com").exists()
    assert (
        Candidate.objects.count(),
        JobOpening.objects.count(),
        Skill.objects.count(),
        Application.objects.count(),
        StageChange.objects.count(),
    ) == first_counts
    assert get_user_model().objects.filter(username="demo").count() == 1
    password = output.split("Password:")[1].split()[0]
    assert get_user_model().objects.get(username="demo").check_password(password)


def test_refuses_to_run_when_debug_is_off(settings):
    settings.DEBUG = False

    with pytest.raises(CommandError, match="development only"):
        load()

    assert not Candidate.objects.exists()
    assert not get_user_model().objects.filter(username="demo").exists()


def test_all_history_comes_from_the_services():
    with (
        patch.object(demo_command, "create_application", wraps=create_application) as creates,
        patch.object(demo_command, "move_application", wraps=move_application) as moves,
    ):
        load()

    # One "recorded" row per create_application call, one row per move_application call:
    # no history row was written any other way.
    assert creates.call_count == Application.objects.count()
    assert moves.call_count == StageChange.objects.exclude(from_stage="").count()
    assert StageChange.objects.filter(from_stage="").count() == Application.objects.count()


def test_every_history_follows_the_stage_rules():
    load()

    for application in Application.objects.all():
        rows = list(application.stage_changes.all())
        assert (rows[0].from_stage, rows[0].to_stage) == ("", Application.Stage.APPLIED)
        for previous, row in zip(rows, rows[1:], strict=False):
            assert row.from_stage == previous.to_stage
            if row.to_stage in CLOSED_STAGES or row.from_stage in CLOSED_STAGES:
                assert row.reason.strip(), f"{application}: {row} has no reason"
        assert rows[-1].to_stage == application.stage


def test_dataset_has_the_promised_people_and_jobs():
    load()

    assert JobOpening.objects.count() == 3
    assert Candidate.objects.count() == 15
    assert Skill.objects.count() >= 5
    assert Candidate.objects.filter(archived=True).count() == 1
    assert (
        Candidate.objects.filter(applications__isnull=False)
        .annotate(n=Count("applications"))
        .filter(n=2)
        .count()
        == 1
    )
    # At least one application was rejected and later reopened, so its timeline shows why.
    reopened = StageChange.objects.filter(from_stage__in=CLOSED_STAGES)
    assert reopened.exists()
    assert get_user_model().objects.get(username="demo").is_superuser is False


def test_reset_deletes_old_resume_files(django_capture_on_commit_callbacks):
    candidate = CandidateFactory()
    candidate.resume.save("cv.pdf", ContentFile(b"%PDF-1.4"), save=True)
    path = Path(candidate.resume.path)
    assert path.exists()

    with django_capture_on_commit_callbacks(execute=True):
        load("--reset")

    assert not path.exists()
