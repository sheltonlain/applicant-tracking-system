from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import JobOpeningForm, SkillForm
from .models import JobOpening, Skill
from .services import (
    STATUS_FILTERS,
    JobStatusError,
    SkillInUseError,
    close_job,
    delete_skill,
    filter_jobs,
    reopen_job,
    skills_with_job_counts,
)

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
        # Where the table's Close / Reopen buttons return to. HTMX searches request this same
        # URL (the one pushed to the address bar), so it is right for both kinds of response.
        "list_url": request.get_full_path(),
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


@require_POST
def skill_add(request):
    """The job form's "+ Add" button (HTMX): create a skill and re-render the skills area.

    The boxes ticked on the form are posted along, so they stay ticked. The job itself is not
    saved here; that still happens when the job form is submitted.
    """
    checked = {int(pk) for pk in request.POST.getlist("skills") if pk.isdigit()}
    new_name = request.POST.get("new_skill", "")
    form = SkillForm(data={"name": new_name})
    if form.is_valid():
        checked.add(form.save().pk)
        new_name = ""
    return render(
        request,
        "jobs/partials/skill_picker.html",
        {
            "skills": Skill.objects.all(),
            "checked": checked,
            "new_skill": new_name,
            "errors": form.errors.get("name", []),
        },
    )


def skill_list(request):
    """The Skills page: every skill with how many jobs use it, plus an "Add skill" form."""
    form = SkillForm(request.POST or None)
    if form.is_valid():
        skill = form.save()
        messages.success(request, f"Skill “{skill.name}” added.")
        return redirect("jobs:skill_list")
    return render(
        request, "jobs/skill_list.html", {"skills": skills_with_job_counts(), "form": form}
    )


def skill_edit(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    form = SkillForm(request.POST or None, instance=skill)
    if form.is_valid():
        form.save()
        messages.success(request, "Skill renamed. The new name shows on every job that uses it.")
        return redirect("jobs:skill_list")
    return render(request, "jobs/skill_form.html", {"form": form, "skill": skill})


@require_POST
def skill_delete(request, pk):
    skill = Skill.objects.filter(pk=pk).first()
    if skill is None:
        # A repeated click or a stale page: a friendly note, not an error page.
        messages.info(request, "That skill was already deleted.")
        return redirect("jobs:skill_list")
    try:
        delete_skill(skill)
    except SkillInUseError as error:
        messages.info(request, str(error))
    else:
        messages.success(request, f"Skill “{skill.name}” deleted.")
    return redirect("jobs:skill_list")


def _change_status(request, pk, service, success_message):
    job = get_object_or_404(JobOpening, pk=pk)
    try:
        service(job)
    except JobStatusError as error:
        # Only happens from a stale page (e.g. a second tab): a friendly note, not an error page.
        messages.info(request, str(error))
    else:
        messages.success(request, f"{job.title}: {success_message}")
    # The job list sends "next" so staff stay on the list; only same-site URLs are followed.
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect(job)
