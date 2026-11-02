from django.db import IntegrityError, transaction
from django.db.models import Count, Q

from candidates.models import Candidate
from jobs.models import JobOpening

from .models import Application, StageChange
from .stages import ACTIVE_STAGES, CLOSED_STAGES, FINAL_STAGES, allowed_moves, find_move


class ApplicationError(Exception):
    """The application can't be recorded (the job is closed, or the candidate already applied)."""


def eligible_jobs(candidate):
    """Open jobs the candidate hasn't applied to yet: the choices for "Add application"."""
    return JobOpening.objects.filter(status=JobOpening.Status.OPEN).exclude(
        applications__candidate=candidate
    )


@transaction.atomic
def create_application(*, candidate, job, source, source_note="", user):
    """Record that the candidate applied to the job, starting in Applied.

    The application and its first history row (no from-stage, to Applied, by `user`) are saved
    together in one transaction, so the timeline always starts when the application was received.

    Raises ApplicationError, and saves nothing, if the candidate is archived, the job is closed, or
    the candidate has already applied to it. The candidate page hides the form for archived
    candidates and its job choices rule out the rest; this guards stale pages and crafted posts.
    """
    # Read from the database, so a candidate archived in another tab is still refused.
    if Candidate.objects.filter(pk=candidate.pk, archived=True).exists():
        raise ApplicationError(
            f"{candidate.full_name} is archived, so new applications can't be added. "
            "Unarchive them first."
        )
    if not job.is_open:
        raise ApplicationError("This job is closed, so new applications can't be added.")
    if Application.objects.filter(candidate=candidate, job=job).exists():
        raise ApplicationError(_already_applied_message(candidate, job))
    try:
        # A savepoint, so the outer transaction stays usable if the database refuses the row.
        with transaction.atomic():
            application = Application.objects.create(
                candidate=candidate,
                job=job,
                source=source,
                source_note=source_note,
                stage=Application.Stage.APPLIED,
            )
    except IntegrityError:
        # Another request recorded the same application between the check and the save.
        raise ApplicationError(_already_applied_message(candidate, job)) from None
    StageChange.objects.create(
        application=application, from_stage="", to_stage=Application.Stage.APPLIED, user=user
    )
    return application


class MoveError(Exception):
    """The stage move isn't allowed by the rules, or is missing a required reason."""


class ReasonRequiredError(MoveError):
    """The move is allowed, but it is a reject, withdraw, or reopen and no reason was given."""


@transaction.atomic
def move_application(application, *, to_stage, user, reason=""):
    """Move the application to `to_stage`, recording who did it, when, and why.

    The stage and its history row are saved in one transaction: both happen or neither does.

    Raises MoveError, and changes nothing, if the stage rules (stages.allowed_moves) don't allow
    the move, or if it is a reject, withdraw, or reopen without a reason. Checked against the
    stage saved in the database, so a stale page or a crafted request can't skip ahead.
    """
    # Re-read (and lock, on databases that support it) so the check uses the current stage.
    application = Application.objects.select_for_update().get(pk=application.pk)
    move = find_move(application, to_stage)
    if move is None:
        raise MoveError(
            f"{application.candidate.full_name} can't be moved from "
            f"{application.get_stage_display()} to {_stage_label(to_stage)}."
        )
    reason = reason.strip()
    if move.needs_reason and not reason:
        raise ReasonRequiredError(f"A reason is required to move to {_stage_label(to_stage)}.")
    from_stage = application.stage
    application.stage = to_stage
    application.save(update_fields=["stage", "updated_at"])
    StageChange.objects.create(
        application=application,
        from_stage=from_stage,
        to_stage=to_stage,
        user=user,
        reason=reason,
    )
    return application


def board_columns(job):
    """The pipeline board for one job: a column per active stage, then one "Closed" column.

    Each column has a key, a label, and its cards; each card is an application plus the moves
    the stage rules allow from where it is, so the template only draws allowed buttons.
    Rejected and withdrawn cards also carry `closed_from`, the label of the stage they were
    closed from. It is read off the reopen move, so the label and the Reopen button always agree.
    """
    applications = job.applications.select_related("candidate").order_by(
        "candidate__last_name", "candidate__first_name", "pk"
    )
    by_stage = {stage: [] for stage in Application.Stage}
    for application in applications:
        moves = allowed_moves(application)
        reopen = next((m for m in moves if m.kind == "reopen"), None)
        by_stage[application.stage].append(
            {
                "application": application,
                "moves": moves,
                "closed_from": reopen.to_stage_label if reopen else None,
            }
        )
    columns = [
        {"key": stage.value, "label": stage.label, "cards": by_stage[stage]}
        for stage in ACTIVE_STAGES
    ]
    closed_cards = [card for stage in FINAL_STAGES for card in by_stage[stage]]
    columns.append({"key": "closed", "label": "Closed", "cards": closed_cards})
    return columns


def open_job_summaries():
    """One summary per open job for the dashboard, newest job first.

    Each summary has the job, `stage_counts` (key, label, and count for each active stage, in
    order), `hired`, and `closed` (Rejected plus Withdrawn). Jobs with no applications get zeros.
    """
    jobs = JobOpening.objects.filter(status=JobOpening.Status.OPEN)
    # One grouped query for every open job's counts, instead of one query per job and stage.
    counts = {}
    for row in (
        Application.objects.filter(job__in=jobs).values("job_id", "stage").annotate(n=Count("pk"))
    ):
        counts[(row["job_id"], row["stage"])] = row["n"]
    return [
        {
            "job": job,
            "stage_counts": [
                {"key": stage.value, "label": stage.label, "count": counts.get((job.pk, stage), 0)}
                for stage in ACTIVE_STAGES
            ],
            "hired": counts.get((job.pk, Application.Stage.HIRED), 0),
            "closed": sum(counts.get((job.pk, stage), 0) for stage in CLOSED_STAGES),
        }
        for job in jobs
    ]


def jobs_needing_attention():
    """Closed jobs that still have at least one application in an active stage.

    Each item has the job and `active`, how many of its applications are still active.
    """
    jobs = (
        JobOpening.objects.filter(status=JobOpening.Status.CLOSED)
        .annotate(active=Count("applications", filter=Q(applications__stage__in=ACTIVE_STAGES)))
        .filter(active__gt=0)
    )
    return [{"job": job, "active": job.active} for job in jobs]


def active_application_count(job):
    """How many of the job's applications are still in an active stage."""
    return job.applications.filter(stage__in=ACTIVE_STAGES).count()


class ArchiveError(Exception):
    """The candidate can't be archived (an application is still active, or already archived)."""


@transaction.atomic
def archive_candidate(candidate):
    """Hide the candidate from the default candidate list.

    Raises ArchiveError, and changes nothing, while any of their applications is in an active
    stage (so nobody disappears mid-process) or if they are already archived (a stale page).
    Their applications and history are not touched.

    Lives here, not in the candidates app, because only this app knows which stages are active.
    """
    # Re-read (and lock, on databases that support it) so the check uses the saved state.
    candidate = Candidate.objects.select_for_update().get(pk=candidate.pk)
    if candidate.archived:
        raise ArchiveError(f"{candidate.full_name} is already archived.")
    active = candidate.applications.filter(stage__in=ACTIVE_STAGES).count()
    if active:
        applications = "application is" if active == 1 else "applications are"
        raise ArchiveError(
            f"{candidate.full_name} can't be archived while {active} {applications} still "
            "active. Move each one to Hired, Rejected, or Withdrawn first."
        )
    candidate.archived = True
    candidate.save(update_fields=["archived", "updated_at"])
    return candidate


def _stage_label(stage):
    # A crafted request may name a stage that doesn't exist; show it as sent instead of crashing.
    return dict(Application.Stage.choices).get(stage, stage)


def _already_applied_message(candidate, job):
    return f"{candidate.full_name} has already applied to {job.title}."
