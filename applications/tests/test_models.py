import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from applications.models import Application
from applications.tests.factories import ApplicationFactory, StageChangeFactory
from candidates.tests.factories import CandidateFactory
from jobs.tests.factories import JobOpeningFactory


def test_database_refuses_a_second_application_for_the_same_candidate_and_job(db):
    candidate = CandidateFactory()
    job = JobOpeningFactory()
    ApplicationFactory(candidate=candidate, job=job)

    with pytest.raises(IntegrityError):
        ApplicationFactory(candidate=candidate, job=job)


def test_same_candidate_can_apply_to_two_jobs_and_two_candidates_to_one_job(db):
    candidate = CandidateFactory()
    job = JobOpeningFactory()

    ApplicationFactory(candidate=candidate, job=job)
    ApplicationFactory(candidate=candidate, job=JobOpeningFactory())
    ApplicationFactory(candidate=CandidateFactory(), job=job)

    assert Application.objects.count() == 3


def test_deleting_a_candidate_or_job_with_applications_is_blocked(db):
    application = ApplicationFactory()

    with pytest.raises(ProtectedError):
        application.candidate.delete()
    with pytest.raises(ProtectedError):
        application.job.delete()
    assert Application.objects.filter(pk=application.pk).exists()


def test_deleting_a_user_with_history_is_blocked(db):
    change = StageChangeFactory()

    with pytest.raises(ProtectedError):
        change.user.delete()


def test_candidate_without_applications_can_still_be_deleted(db):
    candidate = CandidateFactory()

    candidate.delete()  # PROTECT only applies when applications exist
