from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from candidates.models import Candidate
from jobs.models import JobOpening

from .forms import ApplicationForm
from .models import Application
from .services import (
    ApplicationError,
    MoveError,
    board_columns,
    create_application,
    move_application,
)


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


def board(request, job_pk):
    """One job's pipeline board: a column per active stage plus a "Closed" column."""
    job = get_object_or_404(JobOpening, pk=job_pk)
    return render(request, "applications/board.html", _board_context(job))


@require_POST
def move(request, pk):
    """Move one application to the posted `to_stage`, then redraw that job's whole board."""
    application = get_object_or_404(Application.objects.select_related("job"), pk=pk)
    job = application.job
    error = None
    try:
        move_application(
            application,
            to_stage=request.POST.get("to_stage", ""),
            user=request.user,
            reason=request.POST.get("reason", "").strip(),
        )
    except MoveError as exc:
        # A stale board, a double click, or a crafted request: a friendly note, not an error page.
        error = str(exc)
    if request.htmx:
        return render(request, "applications/partials/board.html", _board_context(job, error))
    # Without HTMX (e.g. JavaScript off), go back to the full board and say what happened there.
    if error:
        messages.info(request, error)
    return redirect("applications:board", job_pk=job.pk)


def _board_context(job, error=None):
    return {"job": job, "columns": board_columns(job), "error": error}
