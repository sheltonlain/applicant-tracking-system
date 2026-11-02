import zipfile
from pathlib import Path

from django import forms

from .models import Candidate


class CandidateForm(forms.ModelForm):
    # Email lowercasing and case-insensitive uniqueness are handled by Candidate.clean().
    class Meta:
        model = Candidate
        fields = ["first_name", "last_name", "email", "phone", "url", "notes"]


RESUME_EXTENSIONS = {".pdf", ".docx"}
RESUME_MAX_BYTES = 5 * 1024 * 1024


class ResumeForm(forms.Form):
    # A plain Form, not a ModelForm: a ModelForm would put the new file on the candidate
    # during validation, and replace_resume() needs the old file's name to delete it.
    resume = forms.FileField(label="Résumé")

    def clean_resume(self):
        resume = self.cleaned_data["resume"]
        if Path(resume.name).suffix.lower() not in RESUME_EXTENSIONS:
            raise forms.ValidationError("Upload a PDF or DOCX file.")
        if resume.size > RESUME_MAX_BYTES:
            raise forms.ValidationError("The file is too large. Upload a file of 5 MB or less.")
        if not _content_matches_extension(resume):
            raise forms.ValidationError("Upload a PDF or DOCX file.")
        return resume


def _content_matches_extension(upload):
    """Check the file's contents, not just its name, so a renamed file is turned away.

    A PDF starts with "%PDF-"; a DOCX is a ZIP archive containing word/document.xml.
    """
    try:
        if Path(upload.name).suffix.lower() == ".pdf":
            upload.seek(0)
            return upload.read(5) == b"%PDF-"
        try:
            with zipfile.ZipFile(upload) as archive:
                return "word/document.xml" in archive.namelist()
        except zipfile.BadZipFile:
            return False
    finally:
        upload.seek(0)  # Rewind so the whole file is saved.
