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