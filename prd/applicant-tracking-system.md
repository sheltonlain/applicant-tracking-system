# PRD: Applicant Tracking System (ATS)

## Problem Statement

The company's hiring staff have no single place to track candidates and job applications. Candidates arrive from the company website, job boards, referrals, and other outside sources, and staff need to know who each candidate is, which openings they applied to, how they found each opening, and where every application stands in the hiring process.

Without a shared system, staff cannot easily see the state of a job's pipeline, move applicants forward, or explain later who made a hiring decision, when, and why. Duplicate candidate records creep in, it is unclear what should happen to in-progress applications when a job stops accepting applicants, and there is no agreed way to retire old candidate records without losing history.

## Solution

An internal Django web application, used only by logged-in staff (candidates never log in), that:

- Keeps one record per candidate (identified by a unique email), with contact details, notes, and an optional résumé.
- Lets staff create and edit job openings, tag them with skills, and close or reopen them.
- Records each application of a candidate to a job opening, including how the candidate found that specific job.
- Moves applications through a fixed hiring process (Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, Withdrawn) using clear rules, from a per-job pipeline board that updates without a full page reload.
- Keeps a complete, permanent history of every stage move: who made it, when, and why (a reason is required for rejecting, withdrawing, and reopening).
- Gives staff a home dashboard showing stage counts for every open job, and highlights closed jobs that still have active applications.
- Lets staff archive old candidates instead of deleting them, so lists stay tidy without losing history.

## User Stories

### Access and accounts

1. As a staff member, I want to log in with my username and password, so that only employees can see candidate information.
2. As a staff member, I want every page, including partial page updates and résumé downloads, to require login, so that candidate data is never exposed to someone who isn't signed in.
3. As a staff member, I want to log out, so that nobody else can use my session on a shared computer.
4. As a staff member, I want to reset a forgotten password by email, so that I can regain access without asking an administrator.
5. As a staff member, I want to change my password while logged in, so that I can keep my account secure.
6. As a staff member, I want to see my name in the navigation bar, so that I know which account I am using.
7. As an administrator, I want to create staff accounts in the admin site, so that new hiring team members can use the system.
8. As an administrator, I want to deactivate a departing employee's account, so that they can no longer log in while their past hiring actions remain in the history.
9. As a staff member, I want every staff member to have the same permissions, so that the team can work without waiting on someone with special access.

### Candidates

10. As a staff member, I want to create a candidate with first name, last name, email, phone, LinkedIn/portfolio URL, and notes, so that I have their basic information in one place.
11. As a staff member, I want the system to refuse a second candidate with the same email (ignoring capitalization), so that each person has exactly one record.
12. As a staff member, I want emails saved in lowercase, so that "Jane@Example.com" and "jane@example.com" are treated as the same person.
13. As a staff member, I want to enter phone numbers in any format, so that international and extension numbers are not rejected.
14. As a staff member, I want to edit a candidate's details, including their email, so that I can correct mistakes and keep information current, while the email stays unique.
15. As a staff member, I want to see a candidate's full name displayed from their first and last name, so that records read naturally.
16. As a staff member, I want to upload a résumé (PDF or DOCX, up to 5 MB) for a candidate, so that the hiring team can review their background.
17. As a staff member, I want an upload with the wrong file type or over 5 MB to be rejected with a clear message, so that I know how to fix it.
18. As a staff member, I want uploading a new résumé to replace the old one, so that the candidate always has one current résumé and old files don't pile up.
19. As a staff member, I want to download a candidate's résumé only while logged in, so that personal documents are not publicly accessible.
20. As a staff member, I want two candidates' résumés with the same filename to never overwrite each other, so that files are not mixed up.
21. As a staff member, I want to archive a candidate who is no longer relevant, so that the candidate list stays focused on current people.
22. As a staff member, I want archiving to be blocked while the candidate still has an active application, so that nobody disappears from the list in the middle of a hiring process.
23. As a staff member, I want to unarchive a candidate, so that I can bring back someone who becomes relevant again.
24. As a staff member, I want archived candidates hidden from the default list but viewable with a "Show archived" toggle, so that I can still find them when needed.
25. As a staff member, I want archived candidates' applications and history kept intact, so that past hiring records remain complete.
26. As a staff member, I want there to be no way to permanently delete a candidate who has applications, so that hiring history can never be accidentally destroyed.
27. As a staff member, I want to search candidates by name or email as I type, so that I can find someone quickly without reloading the page.
28. As a staff member, I want the candidate list sorted by last name and split into pages of 25, so that long lists stay manageable.
29. As a staff member, I want my search and filters reflected in the URL, so that I can bookmark a search and use the Back button.

### Job openings and skills

30. As a staff member, I want to create a job opening with title, description, department, location, and employment type (Full-time, Part-time, Contract, Internship), so that postings are clearly described.
31. As a staff member, I want to edit a job opening, so that I can keep its details accurate.
32. As a staff member, I want to create two openings with the same title, so that the same role can be posted for different departments or times.
33. As a staff member, I want department and location shown next to the job title, so that I can tell openings with the same title apart.
34. As a staff member, I want to close a job opening, so that no new applications can be recorded for it.
35. As a staff member, I want applications on a closed job to keep moving through the stages normally, so that we can finish interviewing finalists after we stop accepting applicants.
36. As a staff member, I want to reopen a closed job opening, so that we can resume accepting applicants without touching existing applications.
37. As a staff member, I want the system to record when a job was closed and clear that date when it is reopened, so that I know when hiring stopped.
38. As a staff member, I want hiring someone to leave the job open, so that openings with more than one position can keep hiring.
39. As a staff member, I want a closed job that still has active applications to show a reminder, so that unfinished applications are not forgotten.
40. As a staff member, I want to filter the job list by status (Open, Closed, All) and search by title as I type, so that I can find openings quickly.
41. As a staff member, I want the job list to show the newest openings first, split into pages of 25, so that current openings are easy to reach.
42. As a staff member, I want to attach skills to a job opening, so that the team knows what each role requires.
43. As a staff member, I want the same skill to be shared by many job openings, so that skills are consistent across postings.
44. As a staff member, I want to add a new skill when it doesn't exist yet, so that I am not limited to a fixed list.
45. As a staff member, I want the system to refuse a skill that differs from an existing one only in capitalization, so that the skill list stays clean.
46. As a staff member, I want to rename a skill and have the change appear on every job that uses it, so that fixes apply everywhere at once.
47. As a staff member, I want deleting a skill to be blocked while any job uses it, so that job openings never silently lose skills.

### Applications

48. As a staff member, I want to add an application from a candidate's page by choosing a job opening, so that I can record that they applied.
49. As a staff member, I want the job choices to include only open jobs the candidate hasn't already applied to, so that I can't create invalid applications.
50. As a staff member, I want the system to guarantee that a candidate has at most one application per job opening, so that duplicate applications can never exist.
51. As a staff member, I want to be taken straight to the new candidate's page, ready to add an application, after creating a candidate, so that recording a new applicant feels like one smooth step.
52. As a staff member, I want archived candidates to have no "Add application" option, so that retired records aren't accidentally reused.
53. As a staff member, I want to record how the candidate found this specific job (Company Website, Job Board, Referral, or Other) plus an optional note (for example "LinkedIn" or "Referred by Maria"), so that hiring sources can be counted accurately.
54. As a hiring manager, I want each application to keep its own source, so that a hire is credited to the channel that brought the candidate to that job, even if they first found us elsewhere.
55. As a staff member, I want new applications to start in the Applied stage, so that every application begins at the start of the process.
56. As a staff member, I want a candidate's page to list all their applications with each job and current stage, so that I can see their whole history with the company.

### Pipeline and stage moves

57. As a staff member, I want a home dashboard that shows how many applications are in each stage for every open job, so that I can see the state of hiring at a glance.
58. As a staff member, I want the dashboard to list closed jobs that still have active applications under "Needs attention", so that I can resolve them.
59. As a staff member, I want to click a job on the dashboard to open its pipeline board, so that I can work on that job's applicants.
60. As a staff member, I want a pipeline board per job with a column for each active stage and a column for closed applications (Hired, Rejected, Withdrawn), so that I can see where every applicant is.
61. As a staff member, I want each card to show the candidate's name and how they found the job, so that I recognize applicants quickly.
62. As a staff member, I want each card to offer only the moves that are allowed from its current stage, so that I can't make an invalid move.
63. As a staff member, I want to advance an application one stage at a time (Applied → Screening → Interview → Final Review → Offer → Hired), so that every hire follows the full process.
64. As a staff member, I want to move an application back one stage from any active stage after Applied, so that I can fix a mis-click.
65. As a staff member, I want to reject or withdraw an application from any active stage, so that candidates who leave the process are closed out.
66. As a staff member, I want to give a reason whenever I reject, withdraw, or reopen an application, so that the decision can be explained later.
67. As a staff member, I want the reason form to open in a small dialog right on the board, so that I can give the reason without leaving the page.
68. As a staff member, I want to reopen a rejected or withdrawn application, so that a candidate can be reconsidered.
69. As a staff member, I want a reopened application to return to the stage it was closed from, so that it picks up where it left off.
70. As a staff member, I want to confirm before marking someone Hired, so that a permanent decision isn't made by accident.
71. As a staff member, I want Hired to be permanent, so that hiring records can be trusted.
72. As a staff member, I want the system to refuse skipping stages, moving out of Hired, or any other move not in the rules, even if a request is crafted by hand, so that the data always follows a real hiring path.
73. As a staff member, I want the board, including both affected columns and the counts, to update after a move without reloading the page, so that I can work through many applicants quickly.
74. As a staff member, I want to keep moving applications on a closed job's board, so that unfinished hiring can be completed.

### Stage history

75. As a hiring manager, I want every stage move recorded with the from-stage, to-stage, staff member, time, and reason, so that I can see who did what, when, and why.
76. As a hiring manager, I want the history row for creating an application recorded too, so that the timeline starts when the application was received.
77. As a staff member, I want an application's detail view to show its timeline of stage changes, so that I can understand its history at a glance.
78. As a hiring manager, I want to see whether an application was ever rejected or withdrawn before, and why, so that reconsiderations are informed.
79. As a hiring manager, I want a move to either fully succeed (stage updated and history recorded) or fully fail, so that the history never falls out of step with the current stage.
80. As a hiring manager, I want history to survive a staff member leaving the company, so that past decisions stay attributed to the right person.

### Development and demo

81. As a developer, I want a single command that loads a fixed, realistic demo dataset (jobs in various states, candidates including an archived one and one with two applications, applications in every stage, history with reasons, skills, and a demo login), so that I can click around and demo the system right after setup.
82. As a developer, I want the demo command to refuse to run on a database that already has data unless I explicitly ask it to reset, so that I don't wipe real data by accident.
83. As a developer, I want the demo data to be created through the same move rules the app uses, so that the demo can never contain impossible states.
84. As a developer, I want password-reset emails printed to the terminal during development, so that I can test the reset flow without an email server.

## Implementation Decisions

### Tech stack

- Python, Django, SQLite, uv for environment and dependency management.
- Tailwind CSS with DaisyUI through django-tailwind-cli for styling.
- HTMX for partial page updates, with django-htmx so views can tell HTMX requests apart from full page requests.
- Ruff for linting and formatting (including tests).
- pytest with pytest-django for tests, and factory_boy for test data.

### Project structure

- Three Django apps: **candidates** (Candidate, résumé download), **jobs** (JobOpening, Skill, close/reopen), and **applications** (Application, StageChange, stage rules, pipeline board, dashboard, demo-data command).
- One-way dependency: candidates and jobs never import from applications; applications may import from both. Rules that span apps (for example "a candidate with active applications cannot be archived") are implemented in the applications app's service layer or through reverse relations that need no import.
- Business rules live in a service layer for each app, not in views. Views stay thin: they validate input, call a service, and render a response.
- The stage rules are defined once (stage choices plus a single "allowed moves" function or table) and used by both the services that enforce them and the templates that decide which buttons to show.
- Shared templates (base layout, navigation) live in a project-level templates folder.
- Authentication uses Django's built-in auth app and default user model (no custom user model).

### Models

- **Candidate**: first name, last name, email (required, unique, saved in lowercase), phone (optional, free text, no format validation), LinkedIn/portfolio URL (optional), notes (optional), résumé file (optional), archived flag, created and updated timestamps. Exposes a full-name helper. Default listings exclude archived candidates through a manager or queryset method.
- **JobOpening**: title (not unique), description, department, location, employment type (fixed choices: Full-time, Part-time, Contract, Internship), status (fixed choices: Open, Closed), closed-at timestamp (set on close, cleared on reopen), many-to-many skills, created and updated timestamps.
- **Skill**: name, unique ignoring capitalization. Deleting a skill is blocked while any job uses it.
- **Application**: candidate (protected from deletion), job opening, source (fixed choices: Company Website, Job Board, Referral, Other), optional source note, current stage (fixed choices for the eight stages), timestamps. A database unique constraint ensures one application per candidate per job opening.
- **StageChange**: application, from-stage (empty for the initial "recorded" row), to-stage, staff user (protected from deletion, so users with history can only be deactivated), timestamp, reason (required for reject, withdraw, and reopen; blank otherwise).
- The stage an application was closed from is derived from the latest history row that moved it into Rejected or Withdrawn; no separate field is stored.

### Stage rules

- Active stages, in order: Applied, Screening, Interview, Final Review, Offer. Final stages: Hired, Rejected, Withdrawn.
- Allowed moves from an active stage: forward one stage (Offer moves to Hired), back one stage (not from Applied), Rejected, Withdrawn.
- Allowed moves from Rejected or Withdrawn: reopen to the stage it was closed from.
- No moves from Hired.
- Skipping stages is never allowed.
- Reject, withdraw, and reopen require a non-blank reason.
- All moves go through one service function that checks the rules, updates the stage, and writes the history row inside a single database transaction. Invalid moves raise an error and change nothing.

### Job and candidate lifecycle rules

- Closing a job only blocks new applications. Existing applications on a closed job can still be moved. Reopening only changes the status and clears the closed-at date.
- Hiring does not close the job automatically.
- Archiving a candidate is blocked while they have any application in an active stage. Unarchiving is always allowed. No hard delete of candidates is offered in the app, and the protected relation prevents deleting a candidate with applications even through the admin.

### Résumés

- One résumé per candidate, stored as a file field under a résumés folder in the media root, with randomized file names.
- Form validation accepts only PDF and DOCX files up to 5 MB.
- Replacing a résumé deletes the old file from storage.
- Résumés are served through a login-protected download view, not a public media URL.

### Authentication

- Login and logout use Django's built-in authentication views with DaisyUI-styled templates.
- Password change and the full password reset flow use Django's built-in views. In development, emails go to the console email backend.
- Every view requires login (including HTMX endpoints and résumé downloads) except the login and password-reset pages.
- Accounts are created and deactivated in the Django admin. Inactive users cannot log in.
- The logged-in user is shown in the navigation bar and recorded on every stage change.

### Screens and interactions

- **Home dashboard**: one card per open job showing the count of applications in each active stage plus hired/closed totals, each linking to that job's board. Below it, a "Needs attention" list of closed jobs that still have active applications.
- **Pipeline board (one per job)**: columns for the five active stages plus a "Closed" column grouping Hired, Rejected, and Withdrawn (showing which stage each was closed from). Cards show the candidate name, source, and only the allowed actions: Advance, Back, a Close menu (Reject, Withdraw), Reopen for closed cards, and a locked indicator for Hired. A closed job's board shows a warning when it still has active applications.
- **Moves via HTMX**: each action posts to a move endpoint. On success the server returns the re-rendered board section for that job (all columns and counts), not just the one card. Reject, Withdraw, and Reopen first load a reason form into a modal; Mark Hired loads a confirmation modal. Validation errors are shown in the modal or board without a full page reload.
- **Candidate list**: search by name or email as you type (HTMX request with a short delay that swaps only the results table, with the URL updated), "Show archived" toggle, sorted by last name, 25 per page. The results table is a separate partial template rendered for both full and HTMX requests.
- **Job list**: filter by status (Open, Closed, All) and search by title as you type, using the same HTMX partial pattern, newest first, 25 per page.
- **Candidate detail**: contact details, notes, résumé download/upload, archive/unarchive action (with a clear message when blocked), a list of the candidate's applications with job and current stage, and an "Add application" form (job choice limited to open jobs not yet applied to, plus source and source note). Not shown for archived candidates.
- **After creating a candidate**: redirect to the candidate's detail page with the "Add application" form ready.
- **Application detail**: current stage and a timeline of stage changes (who, when, from, to, reason).
- **Job detail/edit**: fields, skills selection with a way to add a new skill, and close/reopen actions.

### Demo data

- A management command in the applications app loads a fixed, hand-written demo dataset: about three jobs (one closed with active applications), about fifteen candidates (one archived, one with applications to two jobs), applications spread across every stage, history including reasons, several skills, and a development-only demo staff login whose password is printed to the terminal.
- History is created by calling the real move service, not by writing history rows directly.
- The command refuses to run if data already exists unless a reset option is passed.

### Testing approach

- factory_boy factories for each model, kept in each app's tests folder, with unique email sequences and sub-factories for related objects. Tests pass explicitly any values they depend on.
- Shared pytest fixtures for a staff user and a logged-in client.
- Service tests (the largest group): every allowed and every blocked stage move, required reasons, reopen target, transaction behavior, archive rules, close/reopen rules.
- Model tests: unique lowercase email, case-insensitive unique skill names, one application per candidate per job, protected deletions.
- View tests: login required on every view including HTMX endpoints and résumé downloads, HTMX responses return the board or results partial, forms show validation errors, job dropdown filtering, résumé type/size validation.
- Tests that touch uploaded files use a temporary media folder so no files are left behind.

## Out of Scope

- Candidate-facing features of any kind (candidates never log in; no public job board or application form).
- Roles or per-job permissions; every staff member has the same permissions.
- Per-job staff assignment or a hiring-manager field on job openings.
- Logging in with email instead of username (custom user model).
- A staff-managed list of sources; adding a new source category requires a code change.
- Skipping stages, moving out of Hired, or drag-and-drop on the pipeline board.
- A single cross-job table of all applications.
- Required/preferred flags on job skills, and skills on candidates (candidate–job matching).
- Multiple résumés per candidate, résumé version history, or per-application résumés.
- Hard deletion of candidates from the app, and privacy-driven data erasure workflows.
- Automatic actions on job close (auto-rejecting applications) or on hire (auto-closing the job).
- Salary ranges, number of positions, and other job fields beyond those listed.
- Reports and analytics beyond the dashboard stage counts (for example time-in-stage or source reports), although the stored data supports them later.
- Production deployment, a real email service, and production file storage.

## Further Notes

- Throwaway prototypes used to make these decisions are kept in the repository's prototypes folder: candidate source storage, stage-move rules UI, stage-history logic, and pipeline view UI. They are for reference only and must not be promoted into production code.
- Several upgrades were deliberately left easy for later: a staff-managed source list, a combined "new applicant" form on the job board, multiple résumés per candidate, required/preferred skills, and source and time-in-stage reports (the history table already stores the needed data).
- Stage and source values are stored as fixed choices, so changing the list means a code change and migration. This trade-off was accepted for clean, reliable data.
- Next step: break this PRD into implementation phases (for example with the prd-to-plan skill).
