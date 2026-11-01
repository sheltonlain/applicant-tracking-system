from django.db.models import Q

from .models import Candidate


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
