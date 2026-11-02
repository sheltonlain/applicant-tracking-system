from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django_htmx.http import HttpResponseClientRedirect

from candidates.models import Candidate

from .forms import ApplicationForm
from .services import ApplicationError, create_application


def dashboard(request):
    """Home page. A placeholder until the dashboard is built in Phase 11."""
    return render(request, "applications/dashboard.html")


def candidate_applications(request, candidate_pk):
    """The "Applications" panel on a candidate's page: their applications plus the add form.

    The candidate page lazy-loads this panel with HTMX, because the candidates app must not
    import from the applications app. GET draws the panel; POST records a new application.
    """
    candidate = get_object_or_404(Candidate, pk=candidate_pk)
    if not request.htmx:
        # The panel is only a piece of a page; a direct visit gets the whole candidate page.
        return redirect(candidate)

    form = ApplicationForm(request.POST or None, candidate=candidate)
    if form.is_valid():
        job = form.cleaned_data["job"]
        try:
            create_application(
                candidate=candidate,
                job=job,
                source=form.cleaned_data["source"],
                source_note=form.cleaned_data["source_note"],
                user=request.user,
            )
        except ApplicationError as error:
            # Only from a stale page or a double submit: a friendly note, not an error page.
            messages.info(request, str(error))
        else:
            messages.success(request, f"Application to {job} added.")
        # Reload the whole candidate page so the confirmation message shows (base.html).
        return HttpResponseClientRedirect(candidate.get_absolute_url())

    applications = candidate.applications.select_related("job")
    return render(
        request,
        "applications/partials/candidate_applications.html",
        {"candidate": candidate, "form": form, "applications": applications},
    )
