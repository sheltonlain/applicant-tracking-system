from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import JobOpeningForm
from .models import JobOpening
from .services import STATUS_FILTERS, JobStatusError, close_job, filter_jobs, reopen_job

JOBS_PER_PAGE = 25


def job_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status")
    if status not in STATUS_FILTERS:
        status = "open"  # Default, and the fallback for a hand-edited link like ?status=banana.
    jobs = filter_jobs(query, status)
    page_obj = Paginator(jobs, JOBS_PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "status_filters": STATUS_FILTERS,
    }
    # Same pattern as the candidate list: HTMX swaps only the results; Back gets the full page.
    if request.htmx and not request.htmx.history_restore_request:
        return render(request, "jobs/partials/job_results.html", context)
    return render(request, "jobs/job_list.html", context)


def job_create(request):
    form = JobOpeningForm(request.POST or None)
    if form.is_valid():
        job = form.save()
        messages.success(request, "Job opening created.")
        return redirect(job)
    return render(request, "jobs/job_form.html", {"form": form})


def job_detail(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    return render(request, "jobs/job_detail.html", {"job": job})


def job_edit(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    form = JobOpeningForm(request.POST or None, instance=job)
    if form.is_valid():
        form.save()
        messages.success(request, "Job opening updated.")
        return redirect(job)
    return render(request, "jobs/job_form.html", {"form": form, "job": job})


@require_POST
def job_close(request, pk):
    return _change_status(request, pk, close_job, "Job closed. No new applications can be added.")


@require_POST
def job_reopen(request, pk):
    return _change_status(request, pk, reopen_job, "Job reopened. New applications can be added.")


def _change_status(request, pk, service, success_message):
    job = get_object_or_404(JobOpening, pk=pk)
    try:
        service(job)
    except JobStatusError as error:
        # Only happens from a stale page (e.g. a second tab): a friendly note, not an error page.
        messages.info(request, str(error))
    else:
        messages.success(request, success_message)
    return redirect(job)
