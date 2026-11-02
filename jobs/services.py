from django.db.models import Q
from django.utils import timezone

from .models import JobOpening


class JobStatusError(Exception):
    """The job is already in the requested status (e.g. closing a job that is already closed)."""


def close_job(job):
    """Stop accepting new applications for the job and record when that happened.

    Existing applications are not touched. Raises JobStatusError if the job is already closed,
    which can happen when a page was left open in another tab.
    """
    if not job.is_open:
        raise JobStatusError("This job is already closed.")
    job.status = JobOpening.Status.CLOSED
    job.closed_at = timezone.now()
    job.save(update_fields=["status", "closed_at", "updated_at"])


def reopen_job(job):
    """Start accepting new applications again and clear the close date.

    Existing applications are not touched. Raises JobStatusError if the job is already open.
    """
    if job.is_open:
        raise JobStatusError("This job is already open.")
    job.status = JobOpening.Status.OPEN
    job.closed_at = None
    job.save(update_fields=["status", "closed_at", "updated_at"])


# Choices for the job list's status filter, in the order they are shown.
STATUS_FILTERS = {"open": "Open", "closed": "Closed", "all": "All"}


def filter_jobs(query="", status="open"):
    """Jobs with the given status ("open", "closed", or "all") matching the query.

    Every word of the query must appear in the title, department, or location, in any order
    and any capitalization, so "analyst remote" finds a remote Data Analyst.
    """
    jobs = JobOpening.objects.all()
    if status != "all":
        jobs = jobs.filter(status=status)
    for word in query.split():
        jobs = jobs.filter(
            Q(title__icontains=word) | Q(department__icontains=word) | Q(location__icontains=word)
        )
    return jobs
