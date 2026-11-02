---
name: implement
description: Implement one approved phase from a PRD and plan using feedback loops.
argument-hint: "@prd/<feature>.md @plans/<feature>.md implement phase <N>"
disable-model-invocation: true
---

# Implement

## 1. Understand the Phase

Read the referenced PRD and plan. Explore the codebase to understand the relevant files,
patterns, and conventions. If the request does not identify a phase, ask which one.

Implement only that phase. Do not begin the next one.

## 2. Implement the Phase

Run the tdd skill and follow its instructions. Implement any remaining requirements using the project's normal process. 

## 3. Run Feedback Loops

Run the test suite, linter, and formatter. Refactor the code as needed. If the tests fail, fix the issues and re-run the feedback loops until they pass.

## 4. Manual Verification

Outline the steps to manually verify that the implementation meets the requirements. Stop and ask for confirmation before proceeding to the next phase.

## 5. Verify the Acceptance Criteria

Do this only after the user confirms the manual verification. Do not commit or push before
this step is complete.

1. Re-read the phase's acceptance criteria in the referenced plan.
2. For each criterion, name its evidence: a passing test (file and test name) or a manual
   step the user confirmed. Re-run the test suite so the test evidence is current.
3. Show the criteria as a table: criterion, evidence, met or not met.
4. Tick each met criterion in the plan by changing `- [ ]` to `- [x]`. Change only that
   phase's checkboxes and nothing else in the plan.
5. If any criterion is not met or has no evidence, leave it unticked, say what is missing,
   and stop. Do not commit until the gap is fixed or the user explicitly accepts it.
6. Ask the user if CLAUDE.md needs to be updated with any relevant information.

## 6. Finish the Phase

Continue only when every acceptance criterion for the phase is ticked, or the user has
explicitly accepted the unticked ones. Update PROMPTS.md using the format specified in that
file. Then commit the completed phase, including the ticked plan, with a message like
"Implement <feature> phase <N>". Push the commit to GitHub.