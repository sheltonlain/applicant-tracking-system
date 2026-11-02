import io
import zipfile

import pytest
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.urls import reverse

from candidates.models import Candidate
from candidates.tests.factories import CandidateFactory

FIVE_MB = 5 * 1024 * 1024


def fake_pdf(size=100):
    """Bytes that start like a real PDF, padded to the given size."""
    header = b"%PDF-1.7\n"
    return header + b"x" * (size - len(header))


def fake_docx():
    """A minimal ZIP laid out like a Word document."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", "<document/>")
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("resume.txt", b"plain text", "Upload a PDF or DOCX file."),
        (
            "resume.pdf",
            fake_pdf(FIVE_MB + 1),
            "The file is too large. Upload a file of 5 MB or less.",
        ),
        ("resume.pdf", b"not really a pdf", "Upload a PDF or DOCX file."),
        ("resume.docx", b"not really a docx", "Upload a PDF or DOCX file."),
    ],
    ids=["wrong-extension", "over-5mb", "renamed-pdf", "renamed-docx"],
)
def test_wrong_type_or_oversized_resume_is_rejected_with_a_clear_message(
    logged_in_client, filename, content, message
):
    candidate = CandidateFactory()
    upload = SimpleUploadedFile(filename, content)

    response = logged_in_client.post(
        reverse("candidates:resume_upload", args=[candidate.pk]), {"resume": upload}
    )

    assert response.status_code == 200
    assert message in response.content.decode()
    candidate.refresh_from_db()
    assert not candidate.resume


def test_uploading_a_new_resume_replaces_and_deletes_the_old_file(logged_in_client):
    candidate = CandidateFactory()
    url = reverse("candidates:resume_upload", args=[candidate.pk])

    logged_in_client.post(url, {"resume": SimpleUploadedFile("old.pdf", fake_pdf())})
    candidate.refresh_from_db()
    old_name = candidate.resume.name
    assert default_storage.exists(old_name)

    logged_in_client.post(url, {"resume": SimpleUploadedFile("new.docx", fake_docx())})
    candidate.refresh_from_db()

    assert candidate.resume.name != old_name
    assert default_storage.exists(candidate.resume.name)
    assert not default_storage.exists(old_name)


def upload_resume(client, candidate, filename="resume.pdf", content=None):
    content = fake_pdf() if content is None else content
    url = reverse("candidates:resume_upload", args=[candidate.pk])
    return client.post(url, {"resume": SimpleUploadedFile(filename, content)}, follow=True)


def stored_resumes():
    _, files = default_storage.listdir("resumes")
    return sorted(files)


def test_successful_uploads_show_a_friendly_message(logged_in_client):
    candidate = CandidateFactory()

    assert "Résumé uploaded." in upload_resume(logged_in_client, candidate).content.decode()
    assert "Résumé replaced." in upload_resume(logged_in_client, candidate).content.decode()


def test_old_file_that_cannot_be_deleted_still_counts_as_a_successful_replacement(
    logged_in_client, monkeypatch, caplog
):
    candidate = CandidateFactory()
    upload_resume(logged_in_client, candidate, "old.pdf")
    candidate.refresh_from_db()
    old_name = candidate.resume.name

    def file_in_use(self, name):
        raise PermissionError("The file is being used by another process")

    monkeypatch.setattr(FileSystemStorage, "delete", file_in_use)
    response = upload_resume(logged_in_client, candidate, "new.pdf")

    assert "Résumé replaced." in response.content.decode()
    candidate.refresh_from_db()
    assert candidate.resume.name != old_name
    assert default_storage.exists(candidate.resume.name)
    assert "Could not delete unused résumé file" in caplog.text


def test_new_file_that_cannot_be_stored_shows_a_friendly_message_and_keeps_the_old_resume(
    logged_in_client, monkeypatch
):
    candidate = CandidateFactory()
    upload_resume(logged_in_client, candidate, "old.pdf")
    candidate.refresh_from_db()
    old_name = candidate.resume.name

    def disk_full(self, name, content):
        raise OSError("No space left on device")

    monkeypatch.setattr(FileSystemStorage, "_save", disk_full)
    response = upload_resume(logged_in_client, candidate, "new.pdf")

    assert response.status_code == 200
    assert "We couldn&#x27;t save the résumé. Please try again." in response.content.decode()
    candidate.refresh_from_db()
    assert candidate.resume.name == old_name
    assert stored_resumes() == [old_name.removeprefix("resumes/")]


def test_database_failure_shows_a_friendly_message_and_leaves_no_new_file_behind(
    logged_in_client, monkeypatch
):
    candidate = CandidateFactory()
    upload_resume(logged_in_client, candidate, "old.pdf")
    candidate.refresh_from_db()
    old_name = candidate.resume.name

    def database_locked(self, *args, **kwargs):
        raise DatabaseError("database is locked")

    monkeypatch.setattr(Candidate, "save", database_locked)
    response = upload_resume(logged_in_client, candidate, "new.pdf")

    assert "We couldn&#x27;t save the résumé. Please try again." in response.content.decode()
    candidate.refresh_from_db()
    assert candidate.resume.name == old_name
    assert stored_resumes() == [old_name.removeprefix("resumes/")]


def test_same_filename_for_two_candidates_gives_distinct_randomly_named_files(logged_in_client):
    first, second = CandidateFactory(), CandidateFactory()

    upload_resume(logged_in_client, first, "Jane_Doe_Resume.pdf")
    upload_resume(logged_in_client, second, "Jane_Doe_Resume.pdf")
    first.refresh_from_db()
    second.refresh_from_db()

    assert first.resume.name != second.resume.name
    assert default_storage.exists(first.resume.name)
    assert default_storage.exists(second.resume.name)
    for candidate in (first, second):
        assert candidate.resume.name.startswith("resumes/")
        assert candidate.resume.name.endswith(".pdf")
        assert "Jane_Doe_Resume" not in candidate.resume.name


@pytest.mark.parametrize(
    ("filename", "content"),
    [("resume.pdf", fake_pdf()), ("RESUME.DOCX", fake_docx()), ("max.pdf", fake_pdf(FIVE_MB))],
    ids=["pdf", "docx-uppercase", "pdf-exactly-5mb"],
)
def test_pdf_and_docx_up_to_5mb_are_accepted_and_saved_whole(logged_in_client, filename, content):
    candidate = CandidateFactory()

    response = upload_resume(logged_in_client, candidate, filename, content)

    assert response.redirect_chain == [(reverse("candidates:detail", args=[candidate.pk]), 302)]
    candidate.refresh_from_db()
    with candidate.resume.open("rb") as stored:
        assert stored.read() == content


def test_download_returns_the_resume_as_an_attachment(logged_in_client):
    candidate = CandidateFactory(first_name="Jane", last_name="Doe")
    content = fake_pdf()
    upload_resume(logged_in_client, candidate, "anything.pdf", content)

    response = logged_in_client.get(reverse("candidates:resume", args=[candidate.pk]))

    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="Jane-Doe-resume.pdf"'
    assert b"".join(response.streaming_content) == content


def test_download_without_a_resume_returns_404(logged_in_client):
    candidate = CandidateFactory()

    assert (
        logged_in_client.get(reverse("candidates:resume", args=[candidate.pk])).status_code == 404
    )


@pytest.mark.parametrize("name", ["candidates:resume", "candidates:resume_upload"])
def test_resume_views_require_login(client, db, name):
    candidate = CandidateFactory()
    url = reverse(name, args=[candidate.pk])

    response = client.post(url) if name == "candidates:resume_upload" else client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={url}"


def test_detail_page_links_to_download_only_when_a_resume_exists(logged_in_client):
    candidate = CandidateFactory()
    download_link = f'href="{reverse("candidates:resume", args=[candidate.pk])}"'
    detail_url = reverse("candidates:detail", args=[candidate.pk])

    assert download_link not in logged_in_client.get(detail_url).content.decode()
    upload_resume(logged_in_client, candidate)
    assert download_link in logged_in_client.get(detail_url).content.decode()


def test_media_files_are_not_served_at_a_public_url(logged_in_client):
    candidate = CandidateFactory()
    upload_resume(logged_in_client, candidate)
    candidate.refresh_from_db()

    assert logged_in_client.get(f"/media/{candidate.resume.name}").status_code == 404
