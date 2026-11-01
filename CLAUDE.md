# Applicant Tracking System

An internal, staff-only Django web app for tracking candidates, job openings, and applications through a fixed hiring process.

## Tech stack

- Python, Django, SQLite
- Package/environment manager: **uv**
- Tailwind CSS + DaisyUI via django-tailwind-cli
- HTMX + django-htmx for partial page updates
- Ruff (lint + format), pytest + pytest-django + factory_boy (tests)

## Architecture decisions

- Three Django apps: `candidates`, `jobs`, `applications`.
- One-way dependencies: `candidates` and `jobs` never import from `applications`; `applications` may import from both.
- Business rules live in each app's service layer; views stay thin (validate input, call a service, render).
- Stage rules are defined once and shared by the move service and the templates that decide which actions to show.
- All stage moves go through one service function that updates the stage and writes history in a single transaction.
- Django's built-in auth and default User model; every view requires login except login and password-reset pages.
- Stage, source, and other fixed lists are stored as code-defined choices.

## References

- PRD: `prd/applicant-tracking-system.md`
- Implementation plan: `plans/applicant-tracking-system.md`
- Prototypes: `prototypes/` — throwaway, for reference only; never promote into production code.
