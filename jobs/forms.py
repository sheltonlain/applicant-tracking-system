from django import forms

from .models import JobOpening


class JobOpeningForm(forms.ModelForm):
    # Status is left out on purpose: it changes only through the Close / Reopen buttons.
    class Meta:
        model = JobOpening
        fields = ["title", "department", "location", "employment_type", "description"]
