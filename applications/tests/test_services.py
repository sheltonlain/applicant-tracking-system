import pytest
from django.utils import timezone

from applications.models import Application, StageChange
from applications.services import ApplicationError, create_application
from candidates.tests.factories import CandidateFactory
from jobs.models import JobOpening
from jobs.tests.factories import JobOpeningFactory


def test_new_application_starts_in_applied_with_one_recorded_history_row(staff_user):
    candidate = CandidateFactory()
    job = JobOpeningFactory()
    before = timezone.now()

    application = create_application(
        candidate=candidate,
        job=job,
        source=Application.Source.REFERRAL,
        source_note="Referred by Maria",
        user=staff_user,
    )

    application.refresh_from_db()  # saved, not just set on the object
    assert application.candidate == candidate
    assert application.job == job
    assert application.stage == Application.Stage.APPLIED
    assert application.source == Application.Source.REFERRAL
    assert application.source_note == "Referred by Maria"

    history = list(application.stage_changes.all())
    assert len(history) == 1
    recorded = history[0]
    assert recorded.from_stage == ""
    assert recorded.to_stage == Application.Stage.APPLIED
    assert recorded.user == staff_user
    assert recorded.reason == ""
    assert before <= recorded.changed_at <= timezone.now()


def test_create_application_refuses_a_closed_job_or_a_repeat_and_saves_nothing(staff_user):
    candidate = CandidateFactory()
    closed_job = JobOpeningFactory(status=JobOpening.Status.CLOSED)

    with pytest.raises(ApplicationError):
        create_application(
            candidate=candidate,
            job=closed_job,
            source=Application.Source.JOB_BOARD,
            user=staff_user,
        )
    assert not Application.objects.exists()
    assert not StageChange.objects.exists()

    open_job = JobOpeningFactory(status=JobOpening.Status.OPEN)
    create_application(
        candidate=candidate, job=open_job, source=Application.Source.JOB_BOARD, user=staff_user
    )
    with pytest.raises(ApplicationError):
        create_application(
            candidate=candidate, job=open_job, source=Application.Source.OTHER, user=staff_user
        )
    assert Application.objects.count() == 1
    assert StageChange.objects.count() == 1
    assert Application.objects.get().source == Application.Source.JOB_BOARD  # first one kept
