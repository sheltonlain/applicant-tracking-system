# Applicant Tracking System

An internal, staff-only Django web app for tracking candidates, job openings, and applications through a fixed hiring process.

## Tech stack

- Python, Django, SQLite
- Package/environment manager: **uv**
- Tailwind CSS + DaisyUI via django-tailwind-cli
- HTMX + django-htmx for partial page updates
- Ruff (lint + format), pytest + pytest-django + factory_boy (tests)

## Commands

- `uv run python manage.py tailwind runserver` — dev server + Tailwind watcher
- `uv run pytest` — tests
- `uv run ruff check .` / `uv run ruff format .` — lint / format

## Apps

- `config/` — project settings, root URLs, dev console email backend
- `candidates` — Candidate, résumé download
- `jobs` — JobOpening, Skill, close/reopen
- `applications` — Application, StageChange, stage rules, pipeline board, dashboard, demo-data command

## Architecture decisions

- One-way dependencies: `candidates` and `jobs` never import from `applications`; `applications` may import from both.
- Business rules live in each app's service layer; views stay thin (validate input, call a service, render).
- Stage rules are defined once and shared by the move service and the templates that decide which actions to show.
- All stage moves go through one service function that updates the stage and writes history in a single transaction.
- Django's built-in auth and default User model; `LoginRequiredMiddleware` makes every view require login except login and password-reset pages.
- Stage, source, and other fixed lists are stored as code-defined choices.
- HTMX lists: one results partial serves full and HTMX responses; views return the full page for history-restore requests (HTMX history cache is off in `base.html`); page links use `{% querystring %}`.
- Uploaded files are never served at a public URL (no `/media/` route); downloads go through login-protected views, and every test gets a temporary `MEDIA_ROOT` from `conftest.py`.
- `base.html` displays Django messages, so views confirm actions with `messages.success(...)`.
- Job skills use a custom `JobSkill` link table (PROTECT on skill), so the admin edits them through an inline, not a plain field.
- Status changes (job close/reopen, later stage moves) only go through services, never through forms or the admin; a stale or repeated action shows a friendly `messages.info(...)`, not an error page.
- Cross-app UI is lazy-loaded, not imported: the candidate page loads its Applications panel from the `applications` app via HTMX (`hx-trigger="load"`).
- Status-changing actions open a DaisyUI confirmation dialog first; job close/reopen uses the shared `jobs/partials/status_dialog.html` on both the list and detail pages.
- Actions started from a list post a `next` URL to return to it; views follow `next` only if `url_has_allowed_host_and_scheme` accepts it.
- Stage moves post the target stage (`to_stage`), never an action like "advance"; `move_application` re-checks it against the stage saved in the database, so a double-click or stale page gets a friendly note instead of a second move.
- Board buttons come only from `applications/stages.py` `allowed_moves()`; templates may filter which move kinds they draw, but never add a move the rules didn't return.
- A refused HTMX move re-renders `#board` with an inline alert; a refused non-HTMX move redirects to the board with `messages.info(...)`.
- Reject, Withdraw, Reopen, and Mark Hired never post straight from a card: they load a dialog from `GET /applications/<pk>/move/dialog/?to_stage=…` into the `#move-dialog` slot, which sits inside `#board` so redrawing the board after a move also closes the dialog.
- A missing reason raises `ReasonRequiredError` (a `MoveError` subclass); for HTMX the move view re-renders only the dialog with the error (`retarget`/`reswap` to `#move-dialog`) and leaves the board untouched.
- A card's "closed from" label is read off its reopen move from `allowed_moves()`, never a separate lookup, so the label and the Reopen button always agree.
- The job detail page lazy-loads its closed-job warning from `applications` (`applications:job_warning`) via HTMX; the board and job page share `applications/partials/closed_job_warning.html`.
- The board's closed-job warning lives inside `#board`, so every move redraws it, and its count is taken from the board's own active columns.

## References

- PRD: `prd/applicant-tracking-system.md`
- Implementation plan: `plans/applicant-tracking-system.md`
- Prototypes: `prototypes/` — throwaway, for reference only; never promote into production code.
