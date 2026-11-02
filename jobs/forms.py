from django import forms

from .models import JobOpening, Skill


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name"]


class JobOpeningForm(forms.ModelForm):
    # Status is left out on purpose: it changes only through the Close / Reopen buttons.
    class Meta:
        model = JobOpening
        fields = ["title", "department", "location", "employment_type", "description", "skills"]
        # Drawn by jobs/partials/skill_picker.html (checkboxes plus the "+ Add" box).
        widgets = {"skills": forms.CheckboxSelectMultiple}

    def checked_skill_pks(self):
        """The skills to show ticked: the posted ticks, or the job's saved skills."""
        return {int(pk) for pk in self["skills"].value() or [] if str(pk).isdigit()}
