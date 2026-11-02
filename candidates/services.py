import logging

from django.db import DatabaseError
from django.db.models import Q

from .models import Candidate

logger = logging.getLogger(__name__)


# Choices for the candidate list's status filter, in the order they are shown.
STATUS_FILTERS = {"active": "Active", "archived": "Archived", "all": "All"}


def search_candidates(query="", status="active"):
    """Candidates with the given status ("active", "archived", or "all") matching the query.

    Every word of the query must appear in the first name, last name, or email, in any order
    and any capitalization, so "doe jane" finds Jane Doe. A blank query matches everyone.
    """
    if status == "all":
        candidates = Candidate.objects.all()
    elif status == "archived":
        candidates = Candidate.objects.filter(archived=True)
    else:
        candidates = Candidate.objects.not_archived()
    for word in query.split():
        candidates = candidates.filter(
            Q(first_name__icontains=word) | Q(last_name__icontains=word) | Q(email__icontains=word)
        )
    return candidates


class CandidateStatusError(Exception):
    """The candidate is already in the requested state (e.g. unarchiving someone not archived)."""


def unarchive_candidate(candidate):
    """Show the candidate in the default candidate list again. Always allowed.

    Raises CandidateStatusError if they aren't archived, which only happens from a stale page.
    (Archiving lives in applications.services, because it depends on their applications.)
    """
    candidate.refresh_from_db(fields=["archived"])
    if not candidate.archived:
        raise CandidateStatusError(f"{candidate.full_name} is not archived.")
    candidate.archived = False
    candidate.save(update_fields=["archived", "updated_at"])


class ResumeUploadError(Exception):
    """The new résumé could not be saved. The candidate still has their old résumé."""


def replace_resume(candidate, upload):
    """Give the candidate a new résumé and delete the old file from storage.

    Steps, in order: save the new file, point the candidate at it, delete the old file.
    If either of the first two steps fails, nothing changes and ResumeUploadError is raised.
    If only the last step fails, the upload still counts as a success (see _delete_quietly).
    """
    storage = candidate.resume.storage
    old_name = candidate.resume.name
    try:
        candidate.resume.save(upload.name, upload, save=False)
    except OSError as error:
        candidate.resume.name = old_name
        raise ResumeUploadError from error

    new_name = candidate.resume.name
    try:
        candidate.save(update_fields=["resume", "updated_at"])
    except DatabaseError as error:
        _delete_quietly(storage, new_name)  # The new file is not in use, so remove it.
        candidate.resume.name = old_name
        raise ResumeUploadError from error

    if old_name:
        _delete_quietly(storage, old_name)


def _delete_quietly(storage, name):
    """Delete a file that is no longer needed, without failing the request if it can't be.

    On Windows a file that is open (being downloaded, scanned by antivirus) can't be deleted.
    A leftover file is harmless unused disk space, so it is logged instead of shown to staff.
    """
    try:
        storage.delete(name)
    except OSError:
        logger.warning("Could not delete unused résumé file %s", name, exc_info=True)
