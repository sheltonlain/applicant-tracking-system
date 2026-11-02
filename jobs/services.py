from django.db.models import Count, ProtectedError, Q
from django.db.models.functions import Lower
from django.utils import timezone

from .models import JobOpening, Skill


def skills_with_job_counts():
    """Every skill, A to Z, with job_count and its jobs loaded (for the "Used by" list)."""
    # order_by is required: Django ignores Meta.ordering on queries that count (GROUP BY).
    return (
        Skill.objects.annotate(job_count=Count("jobs"))
        .order_by(Lower("name"))
        .prefetch_related("jobs")  # one extra query for all skills, not one per skill
    )


class SkillInUseError(Exception):
    """The skill is attached to at least one job opening, so it can't be deleted."""


def delete_skill(skill):
    """Delete a skill that no job opening uses.

    Raises SkillInUseError (and deletes nothing) while any job uses it, so job openings never
    silently lose skills. The PROTECT link in JobSkill enforces the same rule in the admin.
    """
    job_count = skill.jobs.count()
    if job_count:
        raise SkillInUseError(_in_use_message(skill, job_count))
    try:
        skill.delete()
    except ProtectedError:
        # A job picked up the skill between the count and the delete (e.g. in another tab).
        raise SkillInUseError(_in_use_message(skill, skill.jobs.count())) from None


def _in_use_message(skill, job_count):
    openings = "job opening" if job_count == 1 else "job openings"
    return (
        f"“{skill.name}” is used by {job_count} {openings}, so it can't be deleted. "
        "Remove it from those jobs first."
    )


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
