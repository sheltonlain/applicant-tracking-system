from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRedirect, reswap, retarget

from candidates.models import Candidate
from jobs.models import JobOpening

from .forms import ApplicationForm
from .models import Application
from .services import (
    ApplicationError,
    MoveError,
    ReasonRequiredError,
    active_application_count,
    board_columns,
    create_application,
    jobs_needing_attention,
    move_application,
    open_job_summaries,
)
from .stages import find_move


def dashboard(request):
    """Home page: a card of stage counts per open job, then closed jobs that need attention."""
    return render(
        request,
        "applications/dashboard.html",
        {"summaries": open_job_summaries(), "needs_attention": jobs_needing_attention()},
    )


def job_warning(request, job_pk):
    """The closed-job reminder on a job's detail page (empty when there is nothing to finish).

    The job page lazy-loads it with HTMX, because the jobs app must not import from the
    applications app.
    """
    job = get_object_or_404(JobOpening, pk=job_pk)
    if not request.htmx:
        # The warning is only a piece of a page; a direct visit gets the whole job page.
        return redirect(job)
    return render(
        request,
        "applications/partials/closed_job_warning.html",
        {"job": job, "active_count": active_application_count(job), "show_board_link": True},
    )


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


def detail(request, pk):
    """One application: its current stage and the full timeline of stage changes."""
    application = get_object_or_404(Application.objects.select_related("candidate", "job"), pk=pk)
    history = application.stage_changes.select_related("user")
    return render(
        request,
        "applications/application_detail.html",
        {"application": application, "history": history},
    )


@require_POST
def move(request, pk):
    """Move one application to the posted `to_stage`, then redraw that job's whole board."""
    application = get_object_or_404(Application.objects.select_related("job"), pk=pk)
    job = application.job
    to_stage = request.POST.get("to_stage", "")
    reason = request.POST.get("reason", "").strip()
    error = None
    try:
        move_application(application, to_stage=to_stage, user=request.user, reason=reason)
    except ReasonRequiredError as exc:
        if request.htmx:
            # The move is allowed; only the reason is missing. Keep the dialog open with the
            # error, and leave the board behind it untouched.
            response = _render_move_dialog(
                request, application, find_move(application, to_stage), error=str(exc)
            )
            return reswap(retarget(response, "#move-dialog"), "innerHTML")
        error = str(exc)
    except MoveError as exc:
        # A stale board, a double click, or a crafted request: a friendly note, not an error page.
        error = str(exc)
    if request.htmx:
        return render(request, "applications/partials/board.html", _board_context(job, error))
    # Without HTMX (e.g. JavaScript off), go back to the full board and say what happened there.
    if error:
        messages.info(request, error)
    return redirect("applications:board", job_pk=job.pk)


@require_GET
def move_dialog(request, pk):
    """The dialog for a move that needs one: a reason form, or the Mark Hired confirmation.

    The board loads it into #move-dialog with HTMX; it only shows a form, and the move happens
    when that form posts to `move`. If the stage rules no longer offer the move (a stale board),
    the whole board is redrawn with a note instead.
    """
    application = get_object_or_404(Application.objects.select_related("job", "candidate"), pk=pk)
    job = application.job
    if not request.htmx:
        # The dialog is only a piece of the board; a direct visit gets the whole board.
        return redirect("applications:board", job_pk=job.pk)
    move = find_move(application, request.GET.get("to_stage", ""))
    if move is None or not (move.needs_reason or move.to_stage == Application.Stage.HIRED):
        error = "That move is no longer available, so the board has been refreshed."
        response = render(request, "applications/partials/board.html", _board_context(job, error))
        return reswap(retarget(response, "#board"), "outerHTML")
    return _render_move_dialog(request, application, move)


def _render_move_dialog(request, application, move, error=None):
    return render(
        request,
        "applications/partials/move_dialog.html",
        {"application": application, "move": move, "error": error},
    )


def _board_context(job, error=None):
    columns = board_columns(job)
    # Counted off the drawn columns, so the closed-job warning always agrees with the board.
    active_count = sum(len(column["cards"]) for column in columns if column["key"] != "closed")
    return {"job": job, "columns": columns, "active_count": active_count, "error": error}
