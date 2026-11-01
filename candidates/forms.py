from django import forms

from .models import Candidate


class CandidateForm(forms.ModelForm):
    # Email lowercasing and case-insensitive uniqueness are handled by Candidate.clean().
    class Meta:
        model = Candidate
        fields = ["first_name", "last_name", "email", "phone", "url", "notes"]
