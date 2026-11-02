from pathlib import Path

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CandidateForm, ResumeForm
from .models import Candidate
from .services import (
    STATUS_FILTERS,
    CandidateStatusError,
    ResumeUploadError,
    replace_resume,
    search_candidates,
    unarchive_candidate,
)

CANDIDATES_PER_PAGE = 25


def candidate_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status")
    if status not in STATUS_FILTERS:
        status = "active"  # Default, and the fallback for a hand-edited link like ?status=banana.
    candidates = search_candidates(query, status)
    page_obj = Paginator(candidates, CANDIDATES_PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "status_filters": STATUS_FILTERS,
    }
    # HTMX search requests swap only the results table; normal visits get the whole page.
    # A Back-button history restore also needs the whole page, even though it comes from HTMX.
    if request.htmx and not request.htmx.history_restore_request:
        return render(request, "candidates/partials/candidate_results.html", context)
    return render(request, "candidates/candidate_list.html", context)


def candidate_create(request):
    form = CandidateForm(request.POST or None)
    if form.is_valid():
        candidate = form.save()
        return redirect(candidate)
    return render(request, "candidates/candidate_form.html", {"form": form})


def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(
        request,
        "candidates/candidate_detail.html",
        {"candidate": candidate, "resume_form": ResumeForm()},
    )


@require_POST
def resume_upload(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    form = ResumeForm(request.POST, request.FILES)
    if form.is_valid():
        had_resume = bool(candidate.resume)
        try:
            replace_resume(candidate, form.cleaned_data["resume"])
        except ResumeUploadError:
            form.add_error("resume", "We couldn't save the résumé. Please try again.")
        else:
            messages.success(request, "Résumé replaced." if had_resume else "Résumé uploaded.")
            return redirect(candidate)
    # Show the errors on the detail page, next to the upload box.
    return render(
        request,
        "candidates/candidate_detail.html",
        {"candidate": candidate, "resume_form": form},
    )


def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    form = CandidateForm(request.POST or None, instance=candidate)
    if form.is_valid():
        form.save()
        return redirect(candidate)
    return render(request, "candidates/candidate_form.html", {"form": form, "candidate": candidate})


@require_POST
def candidate_unarchive(request, pk):
    # Archiving is handled by the applications app (applications:archive_candidate), because it
    # is blocked while the candidate has active applications.
    candidate = get_object_or_404(Candidate, pk=pk)
    try:
        unarchive_candidate(candidate)
    except CandidateStatusError as error:
        messages.info(request, str(error))  # A stale page: a friendly note, not an error page.
    else:
        messages.success(request, f"{candidate.full_name} unarchived.")
    return redirect(candidate)


def resume_download(request, pk):
    # Login is enforced by LoginRequiredMiddleware; résumés are never served from a public URL.
    candidate = get_object_or_404(Candidate, pk=pk)
    if not candidate.resume:
        raise Http404("This candidate has no résumé.")
    extension = Path(candidate.resume.name).suffix
    filename = f"{candidate.first_name}-{candidate.last_name}-resume{extension}"
    return FileResponse(candidate.resume.open("rb"), as_attachment=True, filename=filename)
