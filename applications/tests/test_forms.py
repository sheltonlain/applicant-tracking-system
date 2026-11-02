from applications.forms import ApplicationForm
from applications.tests.factories import ApplicationFactory
from candidates.tests.factories import CandidateFactory
from jobs.models import JobOpening
from jobs.tests.factories import JobOpeningFactory


def test_job_choices_are_only_open_jobs_the_candidate_has_not_applied_to(db):
    candidate = CandidateFactory()
    open_job = JobOpeningFactory(status=JobOpening.Status.OPEN)
    JobOpeningFactory(status=JobOpening.Status.CLOSED)
    already_applied = JobOpeningFactory(status=JobOpening.Status.OPEN)
    ApplicationFactory(candidate=candidate, job=already_applied)
    # Another candidate's application doesn't hide the job from this candidate.
    applied_by_someone_else = JobOpeningFactory(status=JobOpening.Status.OPEN)
    ApplicationFactory(job=applied_by_someone_else)

    form = ApplicationForm(candidate=candidate)

    assert set(form.fields["job"].queryset) == {open_job, applied_by_someone_else}
