# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-11-01 — Implemented Phase 1: project skeleton and accounts

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 1`
2. Yes, go ahead with those two
3. Yes, make it pass
4. Switch to the middleware, then move on to behavior 2
5. Yes, keep the test and finish Phase 1 normally. Is there another TDD test we can run for this phase instead?
6. The forgot password link is invalid
7. The dev server is not showing a reset link at all now
8. *(Interrupted a tool call)* I think it is indeed because of the inactive status. Let me try again before we proceed.
9. Everything in Phase 1 works. Update PROMPTS.md, commit with a detailed message, and push.

### Summary
- **Outcome:** Built Phase 1 of the plan. The project is managed with uv on Django 6.1 and uses a `config/` project package. It has the three apps (`candidates`, `jobs`, `applications`), django-htmx, and Tailwind + DaisyUI through django-tailwind-cli. HTMX is saved in `assets/js/` instead of loaded from a CDN. A shared `templates/base.html` has a navbar that shows the user's full name, or the username if no full name is set, with Change password, Admin site (admins only), and Log out. There are DaisyUI-styled templates for login, password change, and the full password-reset flow, plus a login-required placeholder dashboard at `/`. pytest, pytest-django, factory_boy, and Ruff are configured in `pyproject.toml`. The root `conftest.py` has a `UserFactory` and the `staff_user`, `logged_in_client`, and `staff_password` fixtures. The README lists the setup, run, and check commands. 17 tests pass, and Ruff and `manage.py check` are clean. The user manually verified every Phase 1 acceptance criterion.
- **Deviations:**
  - The agent picked two TDD behaviors, both approved: home requires login and shows the username, and the password-reset flow works end to end.
  - After behavior 1 went green with `@login_required`, the agent recommended Django's `LoginRequiredMiddleware`, so every future view requires login by default (user story 2). The user accepted, and the decorator was removed.
  - Follow-up question: asked whether another TDD candidate existed for this phase. The agent said no: the remaining criteria (logout, password change, inactive users, admin) are all built-in Django behavior, so a new test would pass right away.
- **Sideways:**
  - The behavior 2 (password reset) test passed on its first run with no RED. Django's built-in views and the admin app's fallback templates already handled the flow. The agent reported this instead of faking a failure, and the test was kept as a regression check.
  - During manual testing, the reset link in the terminal was "invalid". Django's console email backend printed the email in quoted-printable encoding, which split the long link across two lines with a trailing `=`, so the copied token was broken. The agent reproduced it and wrote a regression test. The test first failed on the real split-link output, after an earlier stub run that only raised an error and didn't count as a RED. The agent then added `config/email.py` (`ReadableConsoleEmailBackend`), which prints the decoded body.
  - Next, no reset email appeared at all. The agent checked the database and found the test `staff` account was inactive (deactivated in manual step 8). Django correctly sends no reset email to inactive users. The user stopped the agent's planned live-server check and confirmed this themselves.
  - A PowerShell-to-Python shell command failed because PowerShell 5.1 strips double quotes from native-command arguments. It was re-run through Bash.

## 2026-11-01 — Created the initial CLAUDE.md from the PRD

### Prompts
1. Create the initial CLAUDE.md file for this project. It should be concise and only about 20-30 lines. Include only the following: (1) a one-line project description, (2) the approved technology stack and package manager, (3) durable, project-wide architecture decisions already established in the PRD, (4) short pointers to the PRD, plan, and prototypes instead of repeating their details. Do not add commands yet because the project tooling has not been installed or verified. Do not predict project structure, paths, template conventions, URL conventions, or testing commands that do not exist yet. Do not copy business requirements, user stories, implementation phases, rejected alternatives, or detailed feature rules into CLAUDE.md. Do not invent new architectural conventions.
2. Add this session to PROMPTS.md

### Summary
- **Outcome:** The agent read the PRD and the start of the plan, then wrote a 26-line `CLAUDE.md` at the repo root. It has a one-line description, the tech stack with uv as package manager, seven architecture decisions taken from the PRD (three apps, one-way imports, thin views with a service layer, stage rules defined once, one transactional move service, default auth with login required everywhere, code-defined choices), and pointers to `prd/`, `plans/`, and `prototypes/` (marked throwaway). Nothing was committed.
- **Deviations:** None. No follow-up questions were asked.
- **Sideways:**
  - The `/clear` before the session meant the agent had to find and read the PRD and plan itself.
  - The agent deliberately left out the plan's URL list and the HTMX lazy-load pattern for "Add application", because those are plan-level details and URL conventions were excluded by the prompt.

## 2026-11-01 — Broke the ATS PRD into a 13-phase tracer-bullet implementation plan

### Prompts
1. `/prd-to-plan`
2. I'd like fewer phases. Can we make the merges tou mentioned?
3. Add this session to PROMPTS.md

### Summary
- **Outcome:** The agent read `prd/applicant-tracking-system.md` and found the repo has no Django code yet. It proposed 16 vertical-slice phases. The plan header records the durable decisions: three apps with one-way imports, namespaced URL patterns using integer pks, the five models and how they relate, a single stage-rules table, and login required everywhere. After the requested merges, it wrote 13 phases to `plans/applicant-tracking-system.md`. Each phase lists its user stories, what to build, and acceptance criteria. No Django code was written and nothing was committed.
- **Deviations:**
  - Asked for fewer phases. The agent's merge suggestions were accepted as offered: password change/reset folded into the project skeleton (old 2 → 1), close/reopen folded into job openings (old 8 → 6), and Mark Hired folded into Reject/Withdraw/Reopen (old 12 → 11).
  - The agent added a decision the PRD doesn't spell out: the candidate page lazy-loads the "Add application" form from the applications app via HTMX. This keeps the one-way import rule. It also chose the specific URL paths. Both were presented with the first breakdown and not objected to.
- **Sideways:**
  - The `/clear` before the skill meant the PRD wasn't in context, so the agent found and read it from `prd/` without asking.
  - The agent caught a confusingly worded acceptance criterion in Phase 12 (about the archive rule and imports) and rewrote it right after writing the file.

## 2026-11-01 — Grilled the ATS project idea into 18 design decisions, prototyped 4 of them, and wrote the PRD

### Prompts
1. `/grill-me @project-idea.md`
2. A
3. a
4. `/prototypes can you please prototype the logic between the options from this question so I can compare them?`
5. Let's go with option A and source on each Application
6. `/prototype can you prototype the UI for options B, C, and your recommendation so I can compare?`
7. B+ but with C's reopen
8. `/prototype can you protoype the logic behind these options for me so I can make my decision?`
9. C
10. Let's go with your recommendation, and I agree - we do not automatically close the job when someone is hired
11. B with all three add-ons
12. Let's do A for now and add the two details you proposed
13. `/prototype can you prototype the ui for each option so I can compare?`
14. Let's go with option A and include the dashboard that shows counts for each open job
15. Option C and add the two details you suggested
16. Option A with all the details you suggested
17. Your recommendation
18. Your recommendation, A with shortcuts
19. b
20. Let's go wtih B and all of the details you suggested
21. Can you explain more about how factory-boy works?
22. Let's go with A, factory_boy plus fixtures
23. Option A with all the details you suggested
24. b
25. `/to-prd`
26. Write this session log to PROMPTS.md according to its instructions.

### Summary
- **Outcome:** Resolved 18 design questions one at a time. Topics were auth/permissions, candidate uniqueness, application source, stage-move rules, stage history, job close/reopen, candidate archiving, skills, the pipeline view, candidate fields, résumé uploads, job fields, the application-recording flow, app structure, accounts/password reset, test data, demo seed data, and list search. Built four throwaway HTML prototypes in `prototypes/`: `candidate-source-logic.html`, `stage-moves-ui.html`, `stage-history-logic.html`, and `pipeline-view-ui.html`. Wrote the PRD to `prd/applicant-tracking-system.md` (84 user stories). Saved one memory note about my preference for prototyping before deciding. No Django code was written and nothing was committed.
- **Deviations:**
  - Q3 (source): chose to store source on each **Application**. The agent's first recommendation was to store it on the Candidate; it changed its mind after the prototype showed what storing it on the Candidate loses.
  - Q4 (stage moves): chose "B+ with C's reopen" (one step forward/back plus reopen). The recommendation was B+ without reopen.
  - Q5 (history): chose **C**, history with required reasons for reject/withdraw/reopen. The recommendation was B, history with no required reasons.
  - Q10 (candidate fields): chose **C**, which adds résumé upload. The recommendation was B, without uploads. This led to an extra Q11 on résumé rules.
  - Q14 (structure): chose **B**, three Django apps. The recommendation was A, one app with a services module. The agent then defined a one-way import rule to make it work.
  - Q15 (accounts): chose **B**, which adds email password reset. The recommendation was A, without it.
  - Q18 (list pages): chose **B**, HTMX search as you type. The recommendation was A, plain GET forms.
  - Follow-ups: asked for prototypes before deciding Q3, Q4, Q5, and Q9. Asked for an explanation of factory_boy before deciding Q16.
- **Sideways:**
  - None of the four prototypes were opened in a browser during the session, so they are untested. A Node smoke test of the first prototype failed because Node isn't installed, and the agent only checked the code by reading it. The two DaisyUI prototypes also depend on a CDN, so they need internet.
  - The agent caught and fixed a wording bug in the step labels of `stage-history-logic.html` ("move backs").
  - Two differently named prototype skills were used (`/prototypes` the first time, `/prototype` after that); both have the same LOGIC/UI instructions.
  - The agent adopted a few defaults without asking, flagged them at the time, and wrote them into the PRD: no separate confirmation for reject (the reason form serves as one), `StageChange.user` on PROTECT, a "Needs attention" list for closed jobs with active applications, and adding django-htmx.