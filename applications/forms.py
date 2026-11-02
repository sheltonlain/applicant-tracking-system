from django import forms

from .models import Application
from .services import eligible_jobs


class ApplicationForm(forms.ModelForm):
    """The "Add application" form on a candidate's page."""

    class Meta:
        model = Application
        fields = ["job", "source", "source_note"]

    def __init__(self, *args, candidate, **kwargs):
        super().__init__(*args, **kwargs)
        # Only open jobs the candidate hasn't applied to. A posted job outside this list (a
        # stale page or a crafted request) fails validation as "not one of the choices".
        self.fields["job"].queryset = eligible_jobs(candidate)
