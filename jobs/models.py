from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse


class Skill(models.Model):
    """A skill shared by many job openings. Names are unique ignoring capitalization."""

    name = models.CharField(max_length=100)

    class Meta:
        ordering = [Lower("name")]
        constraints = [
            # Safety net for code that saves without a form; forms get a friendlier error first.
            models.UniqueConstraint(
                Lower("name"),
                name="unique_skill_name_ignoring_case",
                violation_error_message="A skill with this name already exists.",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        # Runs in every ModelForm (including the admin) before the database rule, so a
        # duplicate in different case gets an error on the name field that names the match.
        self.name = self.name.strip()
        match = Skill.objects.filter(name__iexact=self.name).exclude(pk=self.pk).first()
        if match:
            raise ValidationError({"name": f"A skill named “{match.name}” already exists."})


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
    skills = models.ManyToManyField(Skill, through="JobSkill", blank=True, related_name="jobs")
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


class JobSkill(models.Model):
    """Links a job opening to a skill.

    A custom link table so the skill side can be PROTECT: a skill in use by any job can't be
    deleted anywhere, including the admin. Deleting a job still removes its links.
    """

    job = models.ForeignKey(JobOpening, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["job", "skill"], name="unique_skill_per_job"),
        ]

    def __str__(self):
        return f"{self.skill} on {self.job}"
