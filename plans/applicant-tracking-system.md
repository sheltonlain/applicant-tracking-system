# Plan: Applicant Tracking System (ATS)

> Source PRD: `prd/applicant-tracking-system.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning apps**: three Django apps — `candidates` (Candidate, résumé download), `jobs` (JobOpening, Skill, close/reopen), `applications` (Application, StageChange, stage rules, pipeline board, dashboard, demo-data command).
- **Dependency direction**: one-way. `candidates` and `jobs` never import from `applications`; `applications` may import from both. Cross-app rules (e.g. "can't archive a candidate with active applications") live in the `applications` service layer or use reverse relations that need no import.
- **Service layer**: business rules live in each app's services, not views. Views validate input, call a service, render a response.
- **URLs** (app-namespaced, integer pks, no slugs):
  - `/` — home dashboard (`applications:dashboard`)
  - `/accounts/...` — Django built-in auth views (login, logout, password change, password reset)
  - `/candidates/`, `/candidates/new/`, `/candidates/<pk>/`, `/candidates/<pk>/edit/`, `/candidates/<pk>/resume/`, `/candidates/<pk>/archive/`, `/candidates/<pk>/unarchive/`
  - `/jobs/`, `/jobs/new/`, `/jobs/<pk>/`, `/jobs/<pk>/edit/`, `/jobs/<pk>/close/`, `/jobs/<pk>/reopen/`, `/jobs/skills/...`
  - `/applications/board/<job_pk>/`, `/applications/<pk>/`, `/applications/<pk>/move/`, `/applications/new/<candidate_pk>/`
- **"Add application" on the candidate page**: because `candidates` can't import from `applications`, the candidate detail page lazy-loads the add-application form from the `applications` app via HTMX (`hx-trigger="load"`).
- **Models**:
  - `Candidate` — first/last name, email (unique, stored lowercase), phone (free text), URL, notes, résumé file, archived flag, timestamps; full-name helper; default queryset excludes archived.
  - `JobOpening` — title (not unique), description, department, location, employment type (Full-time/Part-time/Contract/Internship), status (Open/Closed), closed-at, M2M `Skill`, timestamps.
  - `Skill` — name, unique case-insensitively; deletion blocked while any job uses it.
  - `Application` — FK `Candidate` (PROTECT), FK `JobOpening`, source (Company Website/Job Board/Referral/Other), source note, stage (8 choices), timestamps; unique constraint on (candidate, job opening).
  - `StageChange` — FK `Application`, from-stage (blank for the initial row), to-stage, FK `User` (PROTECT), timestamp, reason.
  - "Closed from" stage is derived from the latest history row into Rejected/Withdrawn — no stored field.
- **Stage rules**: defined once (choices + a single allowed-moves function/table), used by both the move service and the templates that decide which buttons to show. All moves go through one service function inside a single transaction.
- **Auth**: Django's default User model. Every view requires login (including HTMX endpoints and résumé downloads) except login and password-reset pages. Accounts are managed in the admin; all staff have equal permissions.
- **Tooling**: uv, SQLite, Tailwind + DaisyUI via django-tailwind-cli, HTMX + django-htmx, Ruff, pytest + pytest-django + factory_boy. Shared templates live in a project-level templates folder.

---

## Phase 1: Project skeleton and accounts

**User stories**: 1, 2, 3, 4, 5, 6, 7, 8, 9, 84

### What to build

A running Django project managed with uv, with the three apps registered, Tailwind/DaisyUI and HTMX wired into a shared base layout, and a navbar showing the logged-in user's name. Staff can log in, log out, change their password, and reset a forgotten password (emails printed to the console). A placeholder home page at `/` requires login. Admins can create and deactivate staff accounts in the Django admin. pytest, factory_boy, and Ruff are configured, with shared fixtures for a staff user and a logged-in client.

### Acceptance criteria

- [x] `uv run` starts the dev server; styled login page appears at `/accounts/login/`
- [x] Anonymous request to `/` redirects to login; logged-in request shows the placeholder home with the username in the navbar
- [x] Logout ends the session
- [x] Password change works while logged in
- [x] Password reset sends an email to the console and the full reset flow completes
- [x] An inactive user cannot log in
- [x] Staff accounts can be created and deactivated in the admin
- [x] `pytest` and `ruff check` run cleanly; staff-user and logged-in-client fixtures exist

---

## Phase 2: Create, view, and edit candidates

**User stories**: 10, 11, 12, 13, 14, 15

### What to build

Staff can create a candidate, see their detail page, and edit them. Emails are saved lowercase and must be unique ignoring case (on both create and edit). Phone accepts any text. The candidate's full name is shown from first and last name. After creating a candidate, staff land on that candidate's detail page.

### Acceptance criteria

- [x] `Candidate` model and migration exist; candidate factory exists
- [x] Creating a candidate redirects to its detail page
- [x] `Jane@Example.com` is stored as `jane@example.com`
- [x] A second candidate with the same email in different case is refused with a form error (create and edit)
- [x] Phone numbers in any format (international, extensions) are accepted
- [x] Detail page shows full name, contact details, and notes
- [x] All candidate views require login

---

## Phase 3: Candidate list with live search

**User stories**: 27, 28, 29

### What to build

A candidate list at `/candidates/`, sorted by last name, 25 per page. A search box filters by name or email as you type: HTMX sends a delayed request that swaps only the results table (a shared partial used for both full and HTMX responses) and updates the URL so searches can be bookmarked and the Back button works.

### Acceptance criteria

- [x] List is sorted by last name and paginated at 25
- [x] Typing in search updates only the results table without a full reload
- [x] The URL reflects the search query; loading that URL directly shows the same results
- [x] HTMX requests receive only the results partial; normal requests receive the full page
- [x] Pagination preserves the search query

---

## Phase 4: Résumés

**User stories**: 16, 17, 18, 19, 20

### What to build

Staff can upload a résumé (PDF or DOCX, up to 5 MB) from the candidate page. Files are stored under a résumés folder with randomized names. Uploading a new résumé replaces and deletes the old file. Downloads go through a login-protected view at `/candidates/<pk>/resume/`, not a public media URL.

### Acceptance criteria

- [x] PDF and DOCX under 5 MB are accepted
- [x] Wrong file type or a file over 5 MB is rejected with a clear message
- [x] Two candidates uploading the same filename get distinct stored files
- [x] Replacing a résumé removes the old file from storage
- [x] The download view requires login; anonymous requests are redirected
- [x] Tests use a temporary media folder and leave no files behind

---

## Phase 5: Job openings with close and reopen

**User stories**: 30, 31, 32, 33, 34, 36, 37, 40, 41

### What to build

Staff can create, view, and edit job openings. Titles need not be unique; department and location are shown next to the title everywhere. The job list at `/jobs/` is newest first, 25 per page, with a status filter (Open/Closed/All) and live title search using the same HTMX partial pattern as candidates. Staff can close a job (recording closed-at) and reopen it (clearing closed-at).

### Acceptance criteria

- [x] `JobOpening` model and migration exist; job factory exists
- [x] Two jobs with the same title can be created
- [x] Department and location appear next to the title in list and detail
- [x] List is newest first, paginated at 25; status filter and live search swap only the results and update the URL
- [x] Closing sets status to Closed and records closed-at; reopening sets Open and clears closed-at
- [x] Close/reopen logic lives in the jobs service layer and is covered by service tests

---

## Phase 6: Skills on job openings

**User stories**: 42, 43, 44, 45, 46, 47

### What to build

Staff can attach skills to a job opening from the job form, and add a new skill when it doesn't exist. Skills are shared across jobs and unique ignoring case. Staff can rename a skill (the change shows on every job using it) and delete a skill only if no job uses it.

### Acceptance criteria

- [x] `Skill` model and M2M migration exist; skill factory exists
- [x] Job form allows selecting skills and adding a new one
- [x] A skill differing only in case from an existing one is refused
- [x] Renaming a skill changes it on every job that uses it
- [x] Deleting a skill in use is blocked with a clear message; an unused skill can be deleted
- [x] Job detail shows its skills

---

## Phase 7: Add an application from the candidate page

**User stories**: 48, 49, 50, 51, 53, 54, 55, 56, 76

### What to build

On the candidate detail page, an "Add application" form (lazy-loaded from the applications app via HTMX) lets staff choose a job, a source, and an optional source note. Job choices include only open jobs the candidate hasn't applied to. New applications start in Applied and get an initial history row (no from-stage) attributed to the logged-in user. The candidate page lists all their applications with job and current stage.

### Acceptance criteria

- [x] `Application` and `StageChange` models and migrations exist, with factories
- [x] Database constraint prevents two applications for the same candidate and job
- [x] Job dropdown excludes closed jobs and jobs already applied to
- [x] New application is in Applied and has one history row with blank from-stage, to-stage Applied, the current user, and a timestamp
- [x] Each application stores its own source and source note
- [x] Candidate page lists applications with job (title, department, location) and stage
- [x] Deleting a candidate with applications is blocked by PROTECT (model test)
- [x] The candidates app does not import from the applications app

---

## Phase 8: Pipeline board with Advance and Back

**User stories**: 35, 60, 61, 62, 63, 64, 72, 73, 74, 75, 79

### What to build

The stage rules table and the single move service, plus a pipeline board at `/applications/board/<job_pk>/`. The board has a column per active stage and a Closed column. Cards show the candidate name and source, with only the allowed buttons. Advance and Back post to `/applications/<pk>/move/` via HTMX; on success the server returns the re-rendered board section (all columns and counts). The move service checks the rules, updates the stage, and writes a history row in one transaction; invalid moves raise an error and change nothing. Boards for closed jobs still allow moves.

### Acceptance criteria

- [x] Stage rules are defined once and used by both the service and the templates
- [x] Every allowed and blocked move from every stage is covered by service tests
- [x] Skipping stages, moving back from Applied, and hand-crafted invalid move requests are refused
- [x] A failed move leaves both stage and history unchanged (transaction test)
- [x] Each successful move writes a history row with from, to, user, and time
- [x] Advance/Back update the whole board section, including counts, without a page reload
- [x] Moves work on a closed job's board
- [x] Board and move endpoints require login

---

## Phase 9: Reject, Withdraw, Reopen, and Mark Hired

**User stories**: 38, 65, 66, 67, 68, 69, 70, 71

### What to build

From any active stage, a Close menu on each card offers Reject and Withdraw; closed cards offer Reopen. Each loads a reason form into a modal on the board; the reason is required. Reopen returns the application to the stage it was closed from (derived from history). Advancing from Offer loads a confirmation modal before marking Hired. Hired cards show a locked indicator and offer no moves. Hiring does not close the job. Closed-column cards show which stage they were closed from.

### Acceptance criteria

- [x] Reject/Withdraw available from every active stage; Reopen only from Rejected/Withdrawn
- [x] Blank reasons are refused, with the error shown in the modal without a page reload
- [x] Reopen returns to the exact stage the application was closed from, including after multiple close/reopen cycles
- [x] Mark Hired requires confirmation in a modal
- [x] No move is possible out of Hired, even via a crafted request
- [x] Hiring leaves the job Open
- [x] Closed-column cards show the stage they were closed from

---

## Phase 10: Application detail timeline

**User stories**: 77, 78, 80

### What to build

An application detail page at `/applications/<pk>/` showing current stage and a full timeline of stage changes (who, when, from, to, reason), including earlier rejections or withdrawals and their reasons. History stays attributed to staff who have since been deactivated. Linked from the candidate page and board cards.

### Acceptance criteria

- [x] Timeline lists every history row in order, starting with the initial "recorded" row
- [x] Reasons for past rejections/withdrawals are visible
- [x] Deactivating a user keeps their name on history rows; deleting a user with history is blocked (PROTECT)
- [x] Detail page requires login

---

## Phase 11: Home dashboard and closed-job reminders

**User stories**: 39, 57, 58, 59

### What to build

Replace the placeholder home page with the dashboard: one card per open job showing counts per active stage plus hired/closed totals, each linking to that job's board. Below, a "Needs attention" list of closed jobs that still have active applications. A closed job's board and detail page show a warning when it still has active applications.

### Acceptance criteria

- [x] Each open job has a card with correct per-stage counts and hired/closed totals
- [x] Cards link to the job's pipeline board
- [x] "Needs attention" lists exactly the closed jobs with at least one active application
- [x] A closed job's board shows a warning when active applications remain
- [x] Dashboard requires login

---

## Phase 12: Archive and unarchive candidates

**User stories**: 21, 22, 23, 24, 25, 26, 52

### What to build

Staff can archive a candidate from their detail page, blocked with a clear message while they have any application in an active stage. Unarchiving is always allowed. Archived candidates are hidden from the default list but shown with a "Show archived" toggle (reflected in the URL). Archived candidates have no "Add application" form. No hard-delete option exists in the app, and applications and history remain intact.

### Acceptance criteria

- [x] Archiving is blocked while the candidate has an active application; allowed once all are Hired/Rejected/Withdrawn
- [x] Unarchive always succeeds
- [x] Default candidate list hides archived; "Show archived" toggle shows them and persists in the URL alongside search
- [x] Archived candidate pages show no "Add application" form, and the endpoint refuses to create one
- [x] Archived candidates' applications and history are unchanged
- [x] The archive rule lives in the applications service layer (or uses a reverse relation); the candidates app still does not import from applications
- [x] No delete action for candidates exists in the app

---

## Phase 13: Demo data command

**User stories**: 81, 82, 83

### What to build

A management command in the applications app that loads a fixed, hand-written dataset: about three jobs (one closed with active applications), about fifteen candidates (one archived, one with two applications), applications in every stage, history with reasons, several skills, and a development-only demo staff login whose password is printed to the terminal. History is created through the real move service. The command refuses to run on a non-empty database unless a reset option is passed.

### Acceptance criteria

- [ ] Running the command on an empty database creates the dataset and prints the demo login
- [ ] Every stage has at least one application; the closed job appears under "Needs attention"
- [ ] All history is created via the move service (no direct history writes)
- [ ] Running on a non-empty database without the reset option refuses and changes nothing
- [ ] Running with the reset option clears and reloads the data
