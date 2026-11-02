"""The hiring-process rules, defined once.

`allowed_moves()` is the single source of truth: the move service refuses anything it does not
list, and the board's templates draw buttons only for the moves it returns.
"""

from dataclasses import dataclass

from .models import Application

Stage = Application.Stage

# The stages an application moves through, in order. Offer advances to Hired.
ACTIVE_STAGES = [
    Stage.APPLIED,
    Stage.SCREENING,
    Stage.INTERVIEW,
    Stage.FINAL_REVIEW,
    Stage.OFFER,
]
# Final stages that can be reopened (back to the stage they were closed from).
CLOSED_STAGES = [Stage.REJECTED, Stage.WITHDRAWN]
# Every final stage, grouped together in the board's "Closed" column.
FINAL_STAGES = [Stage.HIRED, *CLOSED_STAGES]


@dataclass(frozen=True)
class Move:
    """One allowed move: where it goes, and what kind of move it is."""

    to_stage: str
    kind: str  # "advance", "back", "reject", "withdraw", or "reopen"

    @property
    def to_stage_label(self):
        return Stage(self.to_stage).label

    @property
    def needs_reason(self):
        return self.kind in {"reject", "withdraw", "reopen"}


def closed_from_stage(application):
    """The stage a rejected or withdrawn application was closed from, read from its history.

    The latest history row into Rejected or Withdrawn records it; no separate field is stored.
    """
    latest_close = (
        application.stage_changes.filter(to_stage__in=CLOSED_STAGES)
        .order_by("-changed_at", "-pk")
        .first()
    )
    return latest_close.from_stage if latest_close else None


def allowed_moves(application):
    """Every move allowed from the application's current stage."""
    stage = application.stage
    if stage in ACTIVE_STAGES:
        index = ACTIVE_STAGES.index(stage)
        is_last = index == len(ACTIVE_STAGES) - 1
        moves = [Move(Stage.HIRED if is_last else ACTIVE_STAGES[index + 1], "advance")]
        if index > 0:
            moves.append(Move(ACTIVE_STAGES[index - 1], "back"))
        moves.append(Move(Stage.REJECTED, "reject"))
        moves.append(Move(Stage.WITHDRAWN, "withdraw"))
        return moves
    if stage in CLOSED_STAGES:
        reopen_to = closed_from_stage(application)
        return [Move(reopen_to, "reopen")] if reopen_to else []
    return []  # Hired is permanent.


def find_move(application, to_stage):
    """The allowed move to `to_stage` from the application's current stage, or None."""
    return next((m for m in allowed_moves(application) if m.to_stage == to_stage), None)
