from django.db import models
from django.urls import reverse


class Candidate(models.Model):
    """A person who has applied, or may apply, to job openings."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    # Free text on purpose: international numbers and extensions must be accepted.
    phone = models.CharField(max_length=50, blank=True)
    url = models.URLField("LinkedIn / portfolio URL", blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        # Emails identify a person, so "Jane@Example.com" and "jane@example.com" are the same.
        # Also lowercased here for code that saves without a form (e.g. the demo command).
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("candidates:detail", args=[self.pk])

    def clean(self):
        # Runs before Django's uniqueness check in every ModelForm (including the admin),
        # so a duplicate in different case gets a form error instead of a database crash.
        self.email = self.email.lower()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
