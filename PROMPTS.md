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

## 2026-11-01 — Implemented Phase 3: candidate list with live search

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Phase 3`
2. yes, go ahead with those three
3. Can you elaborate more on this choice before I make my decision?
4. go with option B
5. yes, make it pass
6. yes, move on to behavior 2
7. yes, make it pass
8. yes, move on to behavior 3
9. yes, make it pass
10. yes, go ahead
11. I could not get the code to run in the shell.
12. The back button does not work right. When I search jane, then bob, the press back, I return to a page with jane in the box but with the results still for bob
13. The back button works better now. When I press back, the box shows b first, and then when I press back again it shows jane in the box and the table. When I go forward, it again goes to b first and then when I go forward again it is bob in the box and the table
14. *(Answered a multiple-choice question)* Longer pause (Recommended)
15. the back button works now and all other steps passed

### Summary
- **Outcome:** Built Phase 3 of the plan.
  - Added the candidate list at `/candidates/`, sorted by last name then first name, 25 per page, with a "Candidates" link in the navbar.
  - Search lives in a new `candidates/services.py` (`search_candidates`). Every word typed must appear in the first name, last name, or email, ignoring case and word order.
  - The search box is a plain GET form with HTMX added: a 500 ms pause, swapping only `#candidate-results`, and `hx-push-url`. The results table is one partial (`candidates/partials/candidate_results.html`) used for both full pages and HTMX responses.
  - Page links use Django's `{% querystring %}` tag, so they keep the search (and will keep Phase 12's "Show archived" too).
  - The view returns the full page for HTMX Back-button history restores. `base.html` turns off HTMX's history snapshot cache (`historyCacheSize: 0`) app-wide.
  - Added 10 list tests. 43 tests pass and Ruff is clean. The user manually verified every step, and all 5 acceptance criteria were ticked.
- **Deviations:**
  - The agent picked three TDD behaviors, all approved: search by name or email ignoring case, HTMX requests get only the partial, and page links keep the search.
  - Follow-up question: the user asked for more detail on how multi-word searches should work. The agent compared three options with examples (each field separately, every word must match some field, and a joined full name). It recommended B because live search would otherwise empty the list mid-name ("jane d"), and the user chose B. The test was extended and re-approved before going green.
  - Back-button question: the agent offered three options (a longer pause, replacing the URL instead of pushing it, or keeping it as is). The user chose the recommended longer pause.
- **Sideways:**
  - The agent's seed-data snippet for manual testing failed in the interactive Django shell because it had no blank line after the `for` loop. Two more attempts failed on PowerShell 5.1 quoting and an invisible byte-order mark (U+FEFF) added when piping. The agent finally loaded the data from a scratch file through Bash.
  - Manual testing found a Back-button bug the tests had missed: the box showed "jane" while the table showed "bob". After reading the HTMX 2.0.4 source, the agent found that HTMX's localStorage snapshots copy only the page's HTML, which doesn't record typed text. The fix was turning off the snapshot cache so Back re-fetches from the server. The agent noted it had only verified this with tests and reading the source; the user confirmed it in the browser.
  - The user then found extra "b" Back-button steps caused by pauses mid-word under the 300 ms delay. This was resolved by the 500 ms pause the user chose; a long pause mid-word can still add a step.
  - Ruff flagged import spacing in `views.py` once; `ruff check --fix` fixed it.
  - The PROMPTS.md rule says entries are added only by its logging prompt. This entry was written because the `/implement` skill's finish step asks for it.

## 2026-11-01 — Added acceptance-criteria check to the implement skill; verified and committed Phase 2

### Prompts
1. Add code to .claude/skills/implement that ensures we verify and tick off the acceptance criteria in plans/applicant-tracking-system before we commit and push our changes
2. Yes, tick Phase 1 too
3. Manual verification passed, tick Phase 2 and commit

### Summary
- **Outcome:**
  - Added a new step 5, "Verify the Acceptance Criteria", to `.claude/skills/implement/SKILL.md`. After the user confirms manual verification, the agent re-runs the tests, matches each criterion to a passing test or a confirmed manual step, shows a table, and ticks the met criteria in the plan. Any unmet criterion blocks the commit unless the user accepts it. "Finish the Phase" became step 6, and its commit now includes the ticked plan.
  - Ticked all Phase 1 criteria in the plan, based on the user's earlier manual verification recorded below.
  - The user confirmed Phase 2's manual verification. The agent re-ran the suite (33 passed, Ruff clean) and showed all 7 Phase 2 criteria as met, each with named tests and manual steps. It then ticked them and committed and pushed Phase 2.
- **Deviations:** None. The agent suggested ticking Phase 1 too, and the user agreed.
- **Sideways:**
  - The Phase 2 entry below was written before the user confirmed verification, so it says nothing was committed yet. Following the rule against rewriting entries, this new entry records the confirmation and commit instead of editing that one.

## 2026-11-01 — Implemented Phase 2: create, view, and edit candidates

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Implement phase 2`
2. Yes, go ahead with those two
3. Yes, make it pass
4. Yes, move on to behavior 2
5. Yes, accept it as RED and make it pass
6. Is there any way to turn the crash into a friendly message in the admin form you mentioned?
7. Yes, make the clean() change and register Candidate in admin
8. Yes, finish the rest of Phase 2
9. Update PRMOPTS.md

### Summary
- **Outcome:** Built Phase 2 of the plan.
  - Added the `Candidate` model and its migration: first and last name, email (unique, stored lowercase), phone as free text, LinkedIn/portfolio URL, notes, timestamps, and a `full_name` helper.
  - Added `CandidateForm` and the create, detail, and edit views at `/candidates/new/`, `/candidates/<pk>/`, and `/candidates/<pk>/edit/`, with DaisyUI templates. Creating a candidate redirects to their detail page.
  - Lowercasing happens in two places. `Candidate.clean()` runs before Django's uniqueness check, so every model form (the app's and the admin's) shows a friendly email error for a duplicate in different case. `save()` also lowercases, for code that saves without a form.
  - Registered `Candidate` in the admin. Added a "New candidate" button to the navbar. The shared `form_fields.html` partial now renders textareas, for the notes field.
  - Added `CandidateFactory` and view, model, and admin tests. 33 tests pass, and Ruff and `manage.py check` are clean. The manual verification steps were given to the user, but the user had not yet confirmed them when this entry was written. Nothing has been committed yet.
- **Deviations:**
  - The agent picked two TDD behaviors, both approved: (1) creating a candidate stores the email lowercase and redirects to the detail page; (2) a duplicate email in different case is refused with a form error on both create and edit.
  - Follow-up question: the user asked whether the admin could show a friendly message instead of a crash for a duplicate email. The agent recommended moving the lowercasing from `CandidateForm.clean_email()` into `Candidate.clean()` and ranked two other options lower: giving the admin `CandidateForm`, and a database constraint on `Lower("email")`. The user chose the recommendation and also asked to register `Candidate` in the admin, which the plan did not require.
- **Sideways:**
  - Behavior 2's first run failed with an `IntegrityError` (a database crash), not an assertion, so under the TDD rules it was not a clean RED. The agent said so instead of counting it quietly. It explained that the crash *was* the missing behavior, because the form let the duplicate through and the database rejected it. The user accepted it as RED.
  - The first run of the new admin test errored because it lacked the `db` fixture. That was a mechanical fix.
  - To prove the admin test guards something, the agent temporarily disabled `Candidate.clean()`. Both the admin test and the behavior 2 test then crashed with the database error. The agent restored the file and all tests passed again.
  - Ruff's Django rule (DJ012) flagged the model's method order. The agent reordered the methods, with no change in behavior.

## 2026-11-01 — Added commands and app ownership to CLAUDE.md after Phase 1

### Prompts
1. Update CLAUDE.md. Keep it concise and include information regarding useful commands, the Django apps that now exist, and what each app owns. We do not want a verbose explanation. We want to add as little as possible to this file and only include information that is needed while keeping the explanantions basic and to the point.
2. Yes, commit and push it
3. update PROMPTS.md

### Summary
- **Outcome:** `CLAUDE.md` went from 28 to 38 lines. Added a Commands section (dev server with the Tailwind watcher, pytest, Ruff lint and format) and an Apps section that lists `config/` and what each of the three apps owns. This Apps section replaced the old "Three Django apps" bullet. The auth bullet now names `LoginRequiredMiddleware`. Committed and pushed as `390564d`.
- **Deviations:** None. The agent asked before committing, and the user approved.
- **Sideways:**
  - The Apps section lists what each app will own according to the PRD (Candidate, JobOpening, Application, and so on), but those models don't exist yet. The agent pointed this out when presenting the change, and it was kept so that later phases put code in the right app.
  - This session continued from the Phase 1 session below. It got its own entry so the earlier entry stays unchanged.

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