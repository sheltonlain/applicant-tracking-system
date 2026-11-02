from django.db import models
from django.urls import reverse


class JobOpening(models.Model):
    """A position the company is hiring for. Titles are not unique."""

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    # Changed only through jobs.services.close_job() / reopen_job(), never through a form.
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Newest first; pk breaks ties between jobs created in the same instant.
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        # Department and location tell apart openings that share a title.
        return f"{self.title} — {self.department} · {self.location}"

    def get_absolute_url(self):
        return reverse("jobs:detail", args=[self.pk])

    @property
    def is_open(self):
        return self.status == self.Status.OPEN
