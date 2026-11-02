# applicant-tracking-system

An internal, staff-only Django app for tracking candidates, job openings, and applications.

## Setup

```sh
uv sync                                   # install dependencies
uv run python manage.py migrate           # create the SQLite database
uv run python manage.py createsuperuser   # admin account (create staff in /admin/)
```

## Demo data

```sh
uv run python manage.py load_demo_data           # empty database only
uv run python manage.py load_demo_data --reset   # delete candidates, jobs, skills, applications first
```

Loads 3 jobs (one closed with active applications), 15 candidates, applications in every stage,
and a `demo` staff login whose password is printed in the terminal. Development only
(`DEBUG = True`). User accounts are never deleted.

## Run

```sh
uv run python manage.py tailwind runserver   # dev server + Tailwind watcher
```

Open http://127.0.0.1:8000/. Password-reset emails are printed in the terminal.

## Checks

```sh
uv run pytest          # tests
uv run ruff check .    # lint
uv run ruff format .   # format
```
