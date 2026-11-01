from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CandidateForm
from .models import Candidate
from .services import search_candidates

CANDIDATES_PER_PAGE = 25


def candidate_list(request):
    query = request.GET.get("q", "").strip()
    candidates = search_candidates(query)
    page_obj = Paginator(candidates, CANDIDATES_PER_PAGE).get_page(request.GET.get("page"))
    context = {"page_obj": page_obj, "query": query}
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
    return render(request, "candidates/candidate_detail.html", {"candidate": candidate})


def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    form = CandidateForm(request.POST or None, instance=candidate)
    if form.is_valid():
        form.save()
        return redirect(candidate)
    return render(request, "candidates/candidate_form.html", {"form": form, "candidate": candidate})
