from django.db import IntegrityError, transaction

from jobs.models import JobOpening

from .models import Application, StageChange


class ApplicationError(Exception):
    """The application can't be recorded (the job is closed, or the candidate already applied)."""


def eligible_jobs(candidate):
    """Open jobs the candidate hasn't applied to yet: the choices for "Add application"."""
    return JobOpening.objects.filter(status=JobOpening.Status.OPEN).exclude(
        applications__candidate=candidate
    )


@transaction.atomic
def create_application(*, candidate, job, source, source_note="", user):
    """Record that the candidate applied to the job, starting in Applied.

    The application and its first history row (no from-stage, to Applied, by `user`) are saved
    together in one transaction, so the timeline always starts when the application was received.

    Raises ApplicationError, and saves nothing, if the job is closed or the candidate has already
    applied to it. The form's job choices prevent both; this guards stale pages and crafted posts.
    """
    if not job.is_open:
        raise ApplicationError("This job is closed, so new applications can't be added.")
    if Application.objects.filter(candidate=candidate, job=job).exists():
        raise ApplicationError(_already_applied_message(candidate, job))
    try:
        # A savepoint, so the outer transaction stays usable if the database refuses the row.
        with transaction.atomic():
            application = Application.objects.create(
                candidate=candidate,
                job=job,
                source=source,
                source_note=source_note,
                stage=Application.Stage.APPLIED,
            )
    except IntegrityError:
        # Another request recorded the same application between the check and the save.
        raise ApplicationError(_already_applied_message(candidate, job)) from None
    StageChange.objects.create(
        application=application, from_stage="", to_stage=Application.Stage.APPLIED, user=user
    )
    return application


def _already_applied_message(candidate, job):
    return f"{candidate.full_name} has already applied to {job.title}."
