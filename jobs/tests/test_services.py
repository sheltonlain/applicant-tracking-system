import pytest
from django.utils import timezone

from jobs.models import JobOpening
from jobs.services import JobStatusError, close_job, reopen_job
from jobs.tests.factories import JobOpeningFactory


def test_closing_an_open_job_sets_closed_and_records_when_and_refuses_a_second_close(db):
    job = JobOpeningFactory(status=JobOpening.Status.OPEN, closed_at=None)
    before = timezone.now()

    close_job(job)

    job.refresh_from_db()  # the change is saved, not just set on the object
    assert job.status == JobOpening.Status.CLOSED
    assert before <= job.closed_at <= timezone.now()

    first_closed_at = job.closed_at
    with pytest.raises(JobStatusError):
        close_job(job)
    job.refresh_from_db()
    assert job.closed_at == first_closed_at  # the original close date is kept


def test_reopening_a_closed_job_sets_open_and_clears_closed_at_and_refuses_a_second_reopen(db):
    job = JobOpeningFactory(status=JobOpening.Status.CLOSED, closed_at=timezone.now())

    reopen_job(job)

    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN
    assert job.closed_at is None

    with pytest.raises(JobStatusError):
        reopen_job(job)
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN
