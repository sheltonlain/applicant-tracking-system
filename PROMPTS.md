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

## 2026-11-02 — Implemented Phase 10: application detail timeline

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Phase 10`
2. Yes
3. Yes
4. Yes
5. Yes
6. Yes
7. Yes, manual verification passed
8. leave it as is and proceed

### Summary
- **Outcome:** Added the application detail page at `/applications/<pk>/` (`views.detail`, `application_detail.html`). It shows the candidate, the job (department · location), a current-stage badge, the source and note, the applied date, and a DaisyUI timeline of every `StageChange` row, oldest first. Each row shows from → to (the first reads "Recorded → Applied"), the staff member (full name, falling back to username, tagged "deactivated" when inactive), the time, and the reason. The candidate's Applications panel and each board card now have a "Timeline" link. TDD covered two behaviors: every history row in order starting with Recorded, and past reject/withdraw reasons staying visible after reopening. Later tests cover the header details, deactivated users keeping their names, login being required, a 404 for a missing application, and both links. The existing `test_deleting_a_user_with_history_is_blocked` covers PROTECT. All 4 acceptance criteria are ticked, with 249 tests passing. CLAUDE.md was left unchanged at the user's request.
- **Deviations:**
  - The agent proposed two TDD behaviors rather than three, because the login requirement and the deactivated-user name follow existing patterns and would not have gone RED on their own. The user approved.
  - The agent suggested a CLAUDE.md note about timeline attribution and unfiltered history, while leaning against it. The user chose to leave CLAUDE.md as is.
- **Sideways:**
  - The first version of the current-stage test matched the badge by exact class string and whitespace, which was brittle. Before running it, the agent added `id="current-stage"` to the badge and matched with a regex instead.

## 2026-11-02 — Implemented Phase 9: Reject, Withdraw, Reopen, and Mark Hired

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Phase 9`
2. Yes, go ahead with those three
3. yes, make it pass
4. yes, move on to behavior 2
5. yes, make it pass
6. yes, move on to behavior 3
7. yes, make it pass
8. yes, continue with the rest of the phase
9. Manual verification passed, move on to the acceptance criteria
10. Add all three to CLAUDE.md

### Summary
- **Outcome:** Phase 8's move service already enforced reject, withdraw, reopen, and Hired rules, so Phase 9 was mostly board UI. Added `ReasonRequiredError` (a `MoveError` subclass) and `stages.find_move()`, now shared by the service and views. Added a dialog endpoint `GET /applications/<pk>/move/dialog/?to_stage=…` that loads `partials/move_dialog.html` into a `#move-dialog` slot inside `#board`: a reason form for Reject, Withdraw, and Reopen, or a "Hired is permanent" confirmation for Mark Hired. A stale or crafted dialog request redraws the board with a note instead. A blank reason on an HTMX move redraws only the dialog with the error (`retarget`/`reswap`). A successful move redraws the board, which also closes the dialog. Cards gained a Close ▾ menu (Reject…, Withdraw…), Mark Hired… on Offer, ↺ Reopen… on closed cards, and a 🔒 Hired badge. Closed-column badges read e.g. "Rejected · from Interview", taken from the reopen move. TDD covered three behaviors: the blank-reason dialog error, the dialog endpoint for each move, and the "closed from" label. Later tests cover card buttons, a successful reject, the non-HTMX blank reason, stale, skipped, and unknown dialog requests, login, POST refusal, crafted moves out of Hired, hiring leaving the job Open, and reopen across three close/reopen cycles. All 7 acceptance criteria are ticked, with 242 tests passing. Three conventions were added to CLAUDE.md (dialog loading, `ReasonRequiredError` handling, closed-from label source).
- **Deviations:**
  - The agent chose without asking, and stated the choices in the plan before TDD (not objected to): a separate dialog URL instead of inline dialogs per card, and a non-HTMX visit to the dialog URL redirecting to the board rather than a full-page form.
  - During behavior 2 the agent split the stale-board case out of the TDD test into a regular test written afterwards, to keep one test per cycle, and said so when showing the RED test.
  - No follow-up questions or overridden recommendations this session.
- **Sideways:**
  - Behavior 1's first run failed with `KeyError` on a missing response header rather than an assertion. The agent switched to `response.get(...)` (a mechanical fix, noted) to get a real RED.
  - A shell command editing `services.py` hung on the `python3` alias again (same problem as Phases 7 and 8). The agent stopped it, confirmed nothing had changed, and made the edits with the Edit tool.
  - A later shell heredoc adding the remaining tests failed to parse before running. The agent confirmed nothing had been written and added the tests with Edit.
  - The first board template drew both a stage badge and a separate 🔒 Hired badge on Hired cards; the agent merged them before running tests.

## 2026-11-01 — Implemented Phase 8: pipeline board with Advance and Back

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Phase 8`
2. Yes, go ahead with those three
3. yes, make it pass
4. yes, move on to behavior 2
5. yes, make it pass
6. yes, move on to behavior 3
7. yes, make it pass
8. yes, continue with the rest of the phase
9. Manual verification passed, move on to the acceptance criteria
10. Add all three to CLAUDE.md

### Summary
- **Outcome:** Added `applications/stages.py`, the single home of the stage rules. It has `ACTIVE_STAGES`, `allowed_moves(application)`, and `closed_from_stage()`, which reads the reopen target from history. Added `move_application()` to the service layer. In one transaction it re-reads the application, refuses any move `allowed_moves` doesn't list (and reject/withdraw/reopen without a reason) with `MoveError`, saves the stage, and writes the history row. Added the pipeline board at `/applications/board/<job_pk>/`: five active-stage columns plus Closed, each with a count. Cards show the name, source, and note, and only Advance and Back buttons drawn from `allowed_moves`. Added the move endpoint `POST /applications/<pk>/move/`. HTMX requests get the whole `#board` redrawn, with an inline alert if the move is refused; non-HTMX requests redirect to the board. Added a "Pipeline board" button on the job detail page. TDD covered three behaviors: an allowed move writes stage plus history, every move outside the rules is refused and changes nothing (43 parametrized cases), and an HTMX Advance returns the whole board with both columns and counts updated. Later tests cover all 21 allowed moves, required reasons, transaction rollback, the stale double-click, closed jobs, login, and GET refusal. All 8 acceptance criteria are ticked, with 223 tests passing. Three conventions were added to CLAUDE.md (post `to_stage`, buttons only from `allowed_moves`, refused-move handling).
- **Deviations:**
  - The agent chose without asking, and stated the choices in the plan before TDD (not objected to): put the full rules table and the reason check in the service now, rather than in Phase 9, because the rules are defined once. Hide Mark Hired, Reject, Withdraw, and Reopen on the board until Phase 9 adds their dialogs. Post the target stage rather than an action name.
  - No follow-up questions or overridden recommendations this session.
- **Sideways:**
  - The first behavior 2 run took 60 seconds, because each history row in the test setup created a new hashed-password user. The agent switched the setup to reuse `staff_user` (a mechanical test fix, noted at the time), which cut the run to 26 seconds.
  - A shell command to make that edit hung on the bare `python` alias again (the same problem as Phase 7). The agent stopped it, confirmed the file was unchanged, and made the edit with the Edit tool.
  - While making behavior 2 pass, the agent noticed that a made-up stage in a crafted request would crash the error message (`Stage("banana")`), and switched to a safe label lookup.
  - To prove the rollback test was meaningful, the agent briefly removed `@transaction.atomic`, confirmed the test failed, and restored it.

## 2026-11-01 — Implemented Phase 7: add an application from the candidate page

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Phase 7`
2. Yes
3. yes, make it pass
4. yes, move on to behavior 2
5. yes, make it pass
6. yes, move on to behavior 3
7. yes, make it pass
8. yes, continue with the rest of the phase
9. Manual verification passed. I do have some UI changes I want to make before we move on to acceptance criteria. 1. There should be no "new candidate" button on the landing page since this button already lives in candidates. 2. When you select a candidate from the candidates tab and land on their page, there should be a back to all candidates button similarly to what we did with the jobs page. 3. In the jobs page, I would like to be able to mark jobs as opened or closed from the table. A warning box should pop up advising you of the change and confirming your action.
10. Yes, I want the same confirmation box
11. That looks right, move on to the acceptance criteria
12. Add all three to CLAUDE.md

### Summary
- **Outcome:** Added the `Application` and `StageChange` models (migration `0001_initial`, factories). Application has a unique (candidate, job) constraint and PROTECT on candidate, job, and history user. `applications/services.py` gained `eligible_jobs()` and `create_application()`, which saves the application in Applied plus its first history row in one transaction and refuses closed jobs and duplicates with `ApplicationError`. The candidate page lazy-loads an Applications panel (list plus "Add application" form) from `/applications/new/<candidate_pk>/` via HTMX. Form errors show in the panel; success reloads the page with a `messages.success`. In the admin, applications are view-only apart from the source fields, and history is a read-only inline. TDD covered three behaviors: initial Applied plus history row, dropdown filtering, and refusing closed/duplicate jobs. UI changes after manual verification: removed the navbar "New candidate" button, added "← All candidates" on the candidate page, and added Close/Reopen to each jobs-table row behind a DaisyUI confirmation dialog that returns to the same filtered list via a safe `next` URL. The same dialog (shared `jobs/partials/status_dialog.html`) now guards the job detail page's buttons too. Close/reopen success messages now name the job. All 8 acceptance criteria are ticked, with 140 tests passing. Three conventions were added to CLAUDE.md (lazy-loaded cross-app UI, confirmation dialogs for status changes, safe `next` redirects).
- **Deviations:**
  - The agent chose without asking: PROTECT on `Application.job` (the plan only named candidate), an HX-Redirect full reload after a successful add (so `base.html` shows the message), and redirecting a non-HTMX visit to the panel URL back to the candidate page. All were presented in the plan summary before TDD started and not objected to.
  - The UI changes (prompts 9–10) went beyond the Phase 7 plan, at my request. After building the table dialog, the agent offered to use it on the job detail page too, and I accepted.
- **Sideways:**
  - Behavior 1's first run failed with `DoesNotExist` instead of an assertion, because the stub didn't save anything. The agent treated this as missing scaffolding, not a RED, made the stub save the application, and got a real RED (`assert 0 == 1` history rows).
  - Two tests written after the code failed at first because of test bugs, not app bugs. The panel test looked for another candidate's job anywhere in the panel, but that open job correctly appeared in the dropdown. The admin POST test left out the read-only inline's management form. Both tests were fixed.
  - The `IntegrityError` fallback for two simultaneous submits in `create_application` is untested, because a single-threaded test can't reach it. The agent flagged this and kept the code.
  - A shell command meant to replace the table's dialog with the shared include hung, probably on a bare `python` alias. The agent stopped it, confirmed the file was unchanged, and made the edit with the Edit tool.

## 2026-11-01 — Implemented Phase 6: skills on job openings

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Phase 6`
2. *(Rejected a multiple-choice question about how to add a new skill, to clarify)*
3. `/prototype can you prototype the UI for each option so I can compare?`
4. Option B
5. yes, go ahead with those three
6. yes, make it pass
7. yes, move on to behavior 2
8. yes, make it pass
9. yes, move on to behavior 3
10. yes, make it pass
11. Yes
12. When you try to delete a skill, and you get the warning that "x job uses this skill" is there a way for us to show a list of jobs where that skill is in use so it's easier to find?
13. `/prototype can you prototype the UI for these?`
14. B
15. yes, make it pass
16. Everything passes
17. Add that line, then update PROMPTS.md, commit, and push

### Summary
- **Outcome:**
  - Added the `Skill` model, linked to jobs through a custom `JobSkill` table that protects skills (`on_delete=PROTECT`), so a skill a job uses can't be deleted anywhere, including the admin. Migration `jobs/migrations/0002_skills.py` and `SkillFactory` were added.
  - `Skill.clean()` refuses a name that differs only in capitalization, with an error on the name field that names the match ("A skill named "Python" already exists."). A database rule on the lowercase name is the backstop.
  - The job form has skill checkboxes and a "+ Add" box (HTMX, `/jobs/skills/add/`). It creates the skill right away and re-renders the skills area with the new skill ticked, keeping earlier ticks. Enter in the box adds the skill instead of submitting the job form.
  - Added a Skills page at `/jobs/skills/`, linked from the job list. It lists skills A to Z, and each "Used by" count opens a list of the jobs, each linking to that job's edit page. It also has Add, Rename, and Delete. `delete_skill()` in `jobs/services.py` refuses to delete a skill in use with a friendly `messages.info` note. A repeated delete also gets a friendly note.
  - The job detail page shows skill badges. The admin registers `Skill` and shows each job's skills as an inline.
  - The shared form partial gained a `skip=` option so a page can draw one field itself.
  - TDD covered three behaviors: refusing a name that differs only in capitalization, blocking the delete of a skill in use, and the "+ Add" button. The "Used by" list got its own RED/GREEN test.
  - 115 tests pass and Ruff is clean. The user confirmed all 13 manual steps. All six acceptance criteria are ticked. One line was added to `CLAUDE.md` (the `JobSkill` link table and the admin inline).
- **Deviations:**
  - The user rejected the agent's first multiple-choice question about adding a new skill, to clarify, and then asked for a UI prototype. Built `prototypes/add-skill-ui.html` with three variants: a text box saved with the job, an HTMX "Add" button, and a separate Skills page only. The agent recommended A; the user chose **B**, the HTMX "Add" button, accepting that a skill added and then cancelled still exists.
  - After the build, the user asked to see which jobs use a skill when a delete is blocked. The agent offered A (list the jobs in the blocked-delete note), B (the "Used by" count opens a list), or C (both), and recommended A. The user asked for a prototype (`prototypes/skill-in-use-ui.html`) and chose **B**, so the delete note stays plain text.
- **Sideways:**
  - Behavior 1's and behavior 3's first runs failed with exceptions (`KeyError`, `DoesNotExist`), not on assertions. Each test got a mechanical fix so it failed on an assertion before any code was written.
  - The first regular-test run found a real bug: the Skills page wasn't sorted A to Z, because Django ignores `Meta.ordering` on queries that count related rows. Fixed with an explicit `order_by`.
  - The login-required test first sent form data on GET requests, which put it in the redirect URL. Fixed so data is sent only with POST.
  - Ruff flagged the new `JobSkill` model for having no `__str__` (DJ008); one was added.
  - Two older text checks on the Skills page ("1 job<", "0 jobs<") broke when the count became a dropdown. Both were updated as mechanical fixes.
  - Typing a skill name and clicking Save without clicking "+ Add" drops the name. The agent pointed this out and the user didn't ask for a change.
  - Neither prototype was opened by the agent in a browser; the user used both.
  - The agent ran the PROMPTS.md edit and the commit/push in parallel. The edit failed (wrong indentation in the text it was matching), so the Phase 6 commit `dd29282` was pushed without this entry. This entry was then added in a follow-up commit instead of rewriting the pushed commit.

## 2026-11-01 — Implemented Phase 5: job openings with close and reopen

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Phase 5`
2. For the decisions you proposed -- All jobs should either be open or closed. There should never be an unknown status. The button that closes and reopens jobs should toggle back and forth. You should not have the option to close a job that is already closed or open a job that is already open. All other suggestions are fine.
3. yes, make it pass
4. yes, move on to behavior 2
5. yes, make it pass. One thing to note -- I do not want an error to display. Only a friendly message.
6. yes, move on to behavior 3
7. yes, make it pass
8. Can we make it so that searchin for a department or location also yields results?
9. yes, make it pass
10. yes, continue with the rest of the phase
11. everything checked out, go ahead
12. You can add that. Before we update PROMPTS.md, I do want to make a quick addition. When a job is created, I want a seamless way to get back to the full job list through the new job's  page. Right now, you just land on the created job card, and it is a bit awkward to navigate from there.
13. it works, go ahead with PROMPTS.md, commit, and push

### Summary
- **Outcome:** Staff can create, view, and edit job openings at `/jobs/`. Titles need not be unique, and every job is labeled "Title — Department · Location". The job list is newest first, 25 per page, with a status dropdown (Open by default; Open/Closed/All in the URL) and search as you type, using the candidate-list HTMX pattern. The detail page has one Close/Reopen toggle button. `close_job` / `reopen_job` in `jobs/services.py` set and clear `closed_at` and refuse a repeated action; the views turn that refusal into a friendly `messages.info` note. Status is not on the edit form and is read-only in the admin. The shared form partial gained dropdown support; the navbar gained a Jobs link; the detail page gained a "← All job openings" link. TDD covered close, reopen, the status filter combined with search, and (added) department/location search. 94 tests pass; all six acceptance criteria ticked. One line added to `CLAUDE.md` (status changes only through services; stale actions get a friendly message).
- **Deviations:**
  - The agent proposed "an unknown status falls back to Open". The user read this as a job status and said jobs must only be Open or Closed. The agent explained it meant only a hand-edited `?status=` value in the list URL; job status was always limited to two choices.
  - The agent proposed that closing an already-closed job silently does nothing. The user asked instead for a single toggle button and no option to repeat an action, so the services refuse a repeat and the views show a friendly message.
  - The user asked that no error ever display, only a friendly message.
  - The user extended search from title only (PRD story 40) to title, department, or location; done with its own RED/GREEN test.
  - After acceptance, the user asked for a link from a new job's page back to the job list.
- **Sideways:**
  - Behavior 3's first test run failed with `NoReverseMatch` (no job detail page yet), not on an assertion; a basic detail view was added before getting a real RED.
  - Employment type was the first dropdown in the app, and the shared form partial would have drawn it as `<input type="select">`; a select branch was added before the job form was used.

## 2026-11-01 — Implemented Phase 4: résumés

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Phase 4`
2. Yes
3. yes, make it pass
4. How difficult would it be to add the contents check?
5. yes, add the contents check
6. yes, make it pass
7. yes, move on to behavior 2
8. yes, make it pass
9. Can you elaborate on the edge case? I don't want my web app showing errors -- only friendly messages about what went wrong.
10. yes, add both failure changes and the success message
11. yes, go ahead with that version of behavior 3
12. yes, make it pass
13. yes, go ahead
14. everything checked out, go ahead
15. Add a short sentence about each line. After that, proceed with PROMPTS.md, commit, and push

### Summary
- **Outcome:** Candidates can have one résumé (PDF or DOCX, up to 5 MB), uploaded from the detail page and downloaded through a login-protected view at `/candidates/<pk>/resume/`. Validation checks the extension, the size, and the file's contents (PDF header / DOCX zip layout). Files are stored under `media/resumes/` with random names; replacing a résumé deletes the old file through the `replace_resume` service. TDD covered three behaviors: rejection with clear messages, replace-and-delete, and distinct random file names. `base.html` gained a messages area for success messages. All tests use a temporary media folder (autouse fixture). 62 tests pass; all six acceptance criteria ticked. Two lines added to `CLAUDE.md` (no public media URL / temp media in tests; messages in `base.html`).
- **Deviations:**
  - The agent first offered an extension-only type check; the user asked how hard a contents check would be and then asked for it.
  - The user asked about the "delete fails" edge case and asked for friendly messages instead of error pages. Added: a failed old-file delete still counts as success (logged as a warning); a failed save shows "We couldn't save the résumé. Please try again." and keeps the old résumé; success messages "Résumé uploaded." / "Résumé replaced.".
  - Behavior 3 was reworded with the user's approval: Django already avoids name collisions, so the test also checks that stored names are random (the original filename is not on disk), which gave a real RED.
- **Sideways:**
  - A Python edit script wrote `é` in the Windows default encoding, breaking `settings.py`; caught by a SyntaxError and re-encoded as UTF-8. Later edits set UTF-8 explicitly.
  - The random-filename code was written during scaffolding, ahead of behavior 3's test; it was reverted so the test could fail first.
  - Behavior 2's first fix still failed: a `ModelForm` puts the new file on the candidate during validation, so the old name was lost. `ResumeForm` became a plain `Form`.
  - A first draft of the behavior 3 test had a broken last line; rewritten before running.
  - A detail-page test matched the download URL inside the upload URL; fixed by checking for the `href="..."` attribute.
  - The Tailwind message classes were first built from pieces (`alert-{{ tag }}`), which Tailwind can't detect; rewritten with full class names.

## 2026-11-01 — Added the HTMX list pattern to CLAUDE.md after Phase 3

### Prompts
1. Add any relevant rules or architecture that we added during phase 2 or phase 3 to CLAUDE.md. Remember to keep this very concise, to the point, and straighforward. We only want to add information that is absolutely vital to the codebase, and we do not want to make the file verbose.
2. Add it to PROMPTS.md first, then commit and push

### Summary
- **Outcome:** Added one bullet to "Architecture decisions" in `CLAUDE.md`, the HTMX list pattern: one results partial for full and HTMX responses, full page for history-restore requests (HTMX history cache off in `base.html`), and page links using `{% querystring %}`. The Phase 5 job list must follow the same rules. Committed and pushed with this entry.
- **Deviations:** None. The agent asked before committing, and the user asked for this log entry first.
- **Sideways:**
  - Phase 2's email lowercasing in `Candidate.clean()` and `save()` was left out on purpose. It belongs to one model and is already explained in comments in the code.
  - This session continued from the Phase 3 session below. It got its own entry so the earlier entry stays unchanged.

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