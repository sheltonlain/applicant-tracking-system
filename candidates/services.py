import logging

from django.db import DatabaseError
from django.db.models import Q

from .models import Candidate

logger = logging.getLogger(__name__)


def search_candidates(query=""):
    """Candidates matching every word of the query in their first name, last name, or email.

    Word order and capitalization don't matter, so "doe jane" finds Jane Doe.
    A blank query returns everyone.
    """
    candidates = Candidate.objects.all()
    for word in query.split():
        candidates = candidates.filter(
            Q(first_name__icontains=word) | Q(last_name__icontains=word) | Q(email__icontains=word)
        )
    return candidates


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
