from django.conf import settings
from django.db import models

from candidates.models import Candidate
from jobs.models import JobOpening


class Application(models.Model):
    """One candidate applying to one job opening, and where that application stands."""

    class Stage(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        INTERVIEW = "interview", "Interview"
        FINAL_REVIEW = "final_review", "Final Review"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    class Source(models.TextChoices):
        COMPANY_WEBSITE = "company_website", "Company Website"
        JOB_BOARD = "job_board", "Job Board"
        REFERRAL = "referral", "Referral"
        OTHER = "other", "Other"

    # PROTECT on both sides: hiring history can never be deleted by deleting a candidate or job.
    candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT, related_name="applications")
    job = models.ForeignKey(JobOpening, on_delete=models.PROTECT, related_name="applications")
    # How the candidate found this specific job, so each hire is credited to the right channel.
    source = models.CharField(max_length=20, choices=Source.choices)
    source_note = models.CharField(
        max_length=200, blank=True, help_text="Optional, e.g. “LinkedIn” or “Referred by Maria”."
    )
    # Changed only through the applications services, never through a form or the admin.
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.APPLIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"],
                name="unique_application_per_candidate_job",
                violation_error_message="This candidate has already applied to this job.",
            ),
        ]

    def __str__(self):
        return f"{self.candidate} → {self.job}"


class StageChange(models.Model):
    """One row of an application's history: who moved it, from where, to where, when, and why."""

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="stage_changes"
    )
    # Blank only for the first row, written when the application is recorded.
    from_stage = models.CharField(max_length=20, choices=Application.Stage.choices, blank=True)
    to_stage = models.CharField(max_length=20, choices=Application.Stage.choices)
    # PROTECT: staff with history can only be deactivated, so decisions stay attributed.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stage_changes"
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["changed_at", "pk"]

    def __str__(self):
        start = self.get_from_stage_display() or "Recorded"
        return f"{self.application}: {start} → {self.get_to_stage_display()}"
