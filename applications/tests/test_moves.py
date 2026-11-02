import pytest
from django.utils import timezone

from applications.models import Application, StageChange
from applications.services import MoveError, move_application
from applications.tests.factories import ApplicationFactory, StageChangeFactory

Stage = Application.Stage

# The hiring rules, written out by hand so the tests don't just repeat the code's table.
# Rejected applications below were closed from Interview; withdrawn ones from Screening.
EXPECTED_ALLOWED = {
    Stage.APPLIED: {Stage.SCREENING, Stage.REJECTED, Stage.WITHDRAWN},
    Stage.SCREENING: {Stage.INTERVIEW, Stage.APPLIED, Stage.REJECTED, Stage.WITHDRAWN},
    Stage.INTERVIEW: {Stage.FINAL_REVIEW, Stage.SCREENING, Stage.REJECTED, Stage.WITHDRAWN},
    Stage.FINAL_REVIEW: {Stage.OFFER, Stage.INTERVIEW, Stage.REJECTED, Stage.WITHDRAWN},
    Stage.OFFER: {Stage.HIRED, Stage.FINAL_REVIEW, Stage.REJECTED, Stage.WITHDRAWN},
    Stage.HIRED: set(),
    Stage.REJECTED: {Stage.INTERVIEW},
    Stage.WITHDRAWN: {Stage.SCREENING},
}
CLOSED_FROM = {Stage.REJECTED: Stage.INTERVIEW, Stage.WITHDRAWN: Stage.SCREENING}

BLOCKED_MOVES = [
    (from_stage, to_stage)
    for from_stage in Stage
    for to_stage in Stage
    if to_stage not in EXPECTED_ALLOWED[from_stage]
]


def application_in(stage, user):
    """An application sitting in `stage`, with history showing how it got there if closed."""
    application = ApplicationFactory(stage=stage)
    StageChangeFactory(application=application, from_stage="", to_stage=Stage.APPLIED, user=user)
    if stage in CLOSED_FROM:
        StageChangeFactory(
            application=application, from_stage=CLOSED_FROM[stage], to_stage=stage, user=user
        )
    return application


def test_allowed_move_updates_stage_and_writes_one_history_row(staff_user):
    application = ApplicationFactory(stage=Stage.SCREENING)
    StageChangeFactory(application=application, from_stage="", to_stage=Stage.APPLIED)
    StageChangeFactory(application=application, from_stage=Stage.APPLIED, to_stage=Stage.SCREENING)
    before = timezone.now()

    move_application(application, to_stage=Stage.INTERVIEW, user=staff_user)

    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW
    history = list(application.stage_changes.all())
    assert len(history) == 3
    latest = history[-1]
    assert latest.from_stage == Stage.SCREENING
    assert latest.to_stage == Stage.INTERVIEW
    assert latest.user == staff_user
    assert latest.reason == ""
    assert before <= latest.changed_at <= timezone.now()


@pytest.mark.parametrize(("from_stage", "to_stage"), BLOCKED_MOVES)
def test_move_outside_the_rules_is_refused_and_changes_nothing(staff_user, from_stage, to_stage):
    application = application_in(from_stage, staff_user)
    history_before = StageChange.objects.count()

    # A reason is always given, so a refusal can only come from the stage rules.
    with pytest.raises(MoveError):
        move_application(application, to_stage=to_stage, user=staff_user, reason="Crafted request")

    application.refresh_from_db()
    assert application.stage == from_stage
    assert StageChange.objects.count() == history_before


ALLOWED_MOVES = [
    (from_stage, to_stage) for from_stage in Stage for to_stage in EXPECTED_ALLOWED[from_stage]
]


@pytest.mark.parametrize(("from_stage", "to_stage"), ALLOWED_MOVES)
def test_every_allowed_move_succeeds_and_is_recorded(staff_user, from_stage, to_stage):
    application = application_in(from_stage, staff_user)

    move_application(application, to_stage=to_stage, user=staff_user, reason="Because")

    application.refresh_from_db()
    assert application.stage == to_stage
    latest = application.stage_changes.last()
    assert (latest.from_stage, latest.to_stage, latest.user) == (from_stage, to_stage, staff_user)
    assert latest.reason == "Because"


@pytest.mark.parametrize(
    ("from_stage", "to_stage"),
    [
        (Stage.INTERVIEW, Stage.REJECTED),
        (Stage.INTERVIEW, Stage.WITHDRAWN),
        (Stage.REJECTED, Stage.INTERVIEW),  # reopen
    ],
)
@pytest.mark.parametrize("reason", ["", "   "])
def test_reject_withdraw_and_reopen_need_a_reason(staff_user, from_stage, to_stage, reason):
    application = application_in(from_stage, staff_user)
    history_before = StageChange.objects.count()

    with pytest.raises(MoveError, match="reason"):
        move_application(application, to_stage=to_stage, user=staff_user, reason=reason)

    application.refresh_from_db()
    assert application.stage == from_stage
    assert StageChange.objects.count() == history_before


def test_reasons_are_saved_without_surrounding_spaces(staff_user):
    application = application_in(Stage.SCREENING, staff_user)

    move_application(application, to_stage=Stage.REJECTED, user=staff_user, reason="  Not a fit  ")

    assert application.stage_changes.last().reason == "Not a fit"


def test_failed_history_write_rolls_back_the_stage_change(staff_user, monkeypatch):
    application = application_in(Stage.SCREENING, staff_user)
    history_before = StageChange.objects.count()

    def history_write_fails(**kwargs):
        raise RuntimeError("database went away")

    # The stage is saved first, then the history row fails: the stage must roll back too.
    monkeypatch.setattr(StageChange.objects, "create", history_write_fails)
    with pytest.raises(RuntimeError):
        move_application(application, to_stage=Stage.INTERVIEW, user=staff_user)

    application.refresh_from_db()
    assert application.stage == Stage.SCREENING
    assert StageChange.objects.count() == history_before


def test_stale_object_cannot_repeat_a_move(staff_user):
    """Two clicks on the same Advance button: the second is checked against the saved stage."""
    application = application_in(Stage.APPLIED, staff_user)
    stale_copy = Application.objects.get(pk=application.pk)
    move_application(application, to_stage=Stage.SCREENING, user=staff_user)

    # The stale copy still says Applied, so Screening looks like an advance, but it isn't now.
    with pytest.raises(MoveError):
        move_application(stale_copy, to_stage=Stage.SCREENING, user=staff_user)

    application.refresh_from_db()
    assert application.stage == Stage.SCREENING
    assert application.stage_changes.count() == 2
