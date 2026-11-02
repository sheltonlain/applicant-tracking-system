"""Load a fixed, hand-written demo dataset so the app can be clicked around right after setup.

Usage: uv run python manage.py load_demo_data

Every application is recorded and moved through the real services (create_application,
move_application), so the demo can never contain a state the stage rules don't allow.
"""

import logging
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from applications.models import Application
from applications.services import archive_candidate, create_application, move_application
from candidates.models import Candidate
from jobs.models import JobOpening, Skill
from jobs.services import close_job

logger = logging.getLogger(__name__)

Stage = Application.Stage
Source = Application.Source
EmploymentType = JobOpening.EmploymentType

DEMO_USERNAME = "demo"

SKILLS = ["Python", "Django", "SQL", "Figma", "User Research", "Copywriting", "Social Media"]

# key: (title, department, location, employment type, skills, description)
JOBS = {
    "backend": (
        "Backend Developer",
        "Engineering",
        "Remote",
        EmploymentType.FULL_TIME,
        ["Python", "Django", "SQL"],
        "Build and maintain the Django services behind our internal tools.",
    ),
    "designer": (
        "Product Designer",
        "Design",
        "Amarillo, TX",
        EmploymentType.FULL_TIME,
        ["Figma", "User Research"],
        "Design clear, friendly screens for our customer and staff apps.",
    ),
    # Closed after its applications are recorded, while some are still active, so it shows
    # up under "Needs attention" on the dashboard.
    "intern": (
        "Marketing Intern",
        "Marketing",
        "Canyon, TX",
        EmploymentType.INTERNSHIP,
        ["Copywriting", "Social Media"],
        "Help plan and write our social media posts for the summer.",
    ),
}
CLOSED_JOBS = ["intern"]

# (first name, last name, email, phone, url, notes)
CANDIDATES = [
    ("Ava", "Martinez", "ava.martinez@example.com", "(806) 555-0101", "", ""),
    ("Ben", "Carter", "ben.carter@example.com", "806-555-0102", "", "Prefers email contact."),
    (
        "Chloe",
        "Nguyen",
        "chloe.nguyen@example.com",
        "+1 806 555 0103",
        "https://example.com/chloe",
        "Interested in both engineering and design roles.",
    ),
    ("Daniel", "Okafor", "daniel.okafor@example.com", "+44 20 7946 0958", "", ""),
    ("Emily", "Johnson", "emily.johnson@example.com", "(806) 555-0105 ext. 12", "", ""),
    (
        "Farah",
        "Hassan",
        "farah.hassan@example.com",
        "806.555.0106",
        "https://www.linkedin.com/in/farah-hassan",
        "",
    ),
    ("George", "Kim", "george.kim@example.com", "", "", ""),
    (
        "Hannah",
        "Lee",
        "hannah.lee@example.com",
        "(806) 555-0108",
        "https://example.com/hannah",
        "Strong portfolio.",
    ),
    ("Isaac", "Brown", "isaac.brown@example.com", "806-555-0109", "", ""),
    ("Julia", "Rossi", "julia.rossi@example.com", "+39 06 1234 5678", "", ""),
    ("Kevin", "Patel", "kevin.patel@example.com", "(806) 555-0111", "", ""),
    ("Laura", "Smith", "laura.smith@example.com", "", "", "Available only for the summer."),
    ("Marcus", "Green", "marcus.green@example.com", "806-555-0113", "", ""),
    ("Nina", "Alvarez", "nina.alvarez@example.com", "(806) 555-0114", "", ""),
    (
        "Omar",
        "Farouk",
        "omar.farouk@example.com",
        "806-555-0115",
        "",
        "Moved away; kept for the record.",
    ),
]
# Archived after their only application is closed (archiving is refused while one is active).
ARCHIVED = ["omar.farouk@example.com"]

ADVANCE_TO_OFFER = [Stage.SCREENING, Stage.INTERVIEW, Stage.FINAL_REVIEW, Stage.OFFER]

# (candidate email, job key, source, source note, moves). Each move is a target stage, or a
# (target stage, reason) pair for the moves that need a reason (reject, withdraw, reopen).
APPLICATIONS = [
    ("ava.martinez@example.com", "backend", Source.JOB_BOARD, "LinkedIn", []),
    ("ben.carter@example.com", "backend", Source.COMPANY_WEBSITE, "", [Stage.SCREENING]),
    (
        "chloe.nguyen@example.com",
        "backend",
        Source.REFERRAL,
        "Referred by Maria",
        [Stage.SCREENING, Stage.INTERVIEW],
    ),
    (
        "daniel.okafor@example.com",
        "backend",
        Source.JOB_BOARD,
        "Indeed",
        [Stage.SCREENING, Stage.INTERVIEW, Stage.FINAL_REVIEW],
    ),
    ("emily.johnson@example.com", "backend", Source.REFERRAL, "Referred by Sam", ADVANCE_TO_OFFER),
    (
        "farah.hassan@example.com",
        "backend",
        Source.COMPANY_WEBSITE,
        "",
        [*ADVANCE_TO_OFFER, Stage.HIRED],
    ),
    (
        "george.kim@example.com",
        "backend",
        Source.JOB_BOARD,
        "",
        [
            Stage.SCREENING,
            Stage.INTERVIEW,
            (Stage.REJECTED, "Not enough Django experience for this role."),
        ],
    ),
    # Rejected, then reopened: shows a past rejection and its reason on the timeline.
    (
        "hannah.lee@example.com",
        "backend",
        Source.OTHER,
        "Met at a career fair",
        [
            Stage.SCREENING,
            (Stage.REJECTED, "Résumé didn't show backend work."),
            (Stage.SCREENING, "Hiring manager asked to reconsider after reviewing the portfolio."),
            Stage.INTERVIEW,
        ],
    ),
    # Chloe's second application: the same person applying to two jobs.
    ("chloe.nguyen@example.com", "designer", Source.COMPANY_WEBSITE, "", []),
    ("isaac.brown@example.com", "designer", Source.JOB_BOARD, "Dribbble", [Stage.SCREENING]),
    (
        "julia.rossi@example.com",
        "designer",
        Source.REFERRAL,
        "Referred by Priya",
        [Stage.SCREENING, Stage.INTERVIEW, (Stage.WITHDRAWN, "Accepted another offer.")],
    ),
    ("kevin.patel@example.com", "designer", Source.COMPANY_WEBSITE, "", ADVANCE_TO_OFFER),
    ("laura.smith@example.com", "intern", Source.OTHER, "University job fair", []),
    (
        "marcus.green@example.com",
        "intern",
        Source.COMPANY_WEBSITE,
        "",
        [Stage.SCREENING, Stage.INTERVIEW],
    ),
    (
        "nina.alvarez@example.com",
        "intern",
        Source.JOB_BOARD,
        "Handshake",
        [Stage.SCREENING, (Stage.REJECTED, "Not available for the full summer schedule.")],
    ),
    (
        "omar.farouk@example.com",
        "intern",
        Source.REFERRAL,
        "Referred by a current intern",
        [(Stage.WITHDRAWN, "Moved out of state.")],
    ),
]


class Command(BaseCommand):
    help = "Load a fixed demo dataset and a demo staff login (development only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all candidates, jobs, skills, and applications first, then load.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo data is for development only; this needs DEBUG = True.")
        if self._has_data() and not options["reset"]:
            raise CommandError(
                "The database already has candidates, jobs, skills, or applications. "
                "Run again with --reset to delete them and load the demo data."
            )

        # One transaction: if anything fails, the old data is kept and nothing half-loads.
        with transaction.atomic():
            if options["reset"]:
                self._delete_data()
            user, password = self._demo_user()
            self._load(user)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data loaded: {len(JOBS)} jobs, {len(CANDIDATES)} candidates, "
                f"{len(APPLICATIONS)} applications."
            )
        )
        self.stdout.write("Log in with this development-only account:")
        self.stdout.write(f"  Username: {DEMO_USERNAME}")
        self.stdout.write(f"  Password: {password}")

    def _has_data(self):
        """Whether any hiring data exists. User accounts don't count (e.g. your superuser)."""
        return any(model.objects.exists() for model in (Application, Candidate, JobOpening, Skill))

    def _delete_data(self):
        """Delete every application (and its history), candidate, job, and skill.

        User accounts are kept. Order matters: applications PROTECT their candidate and job,
        and job links PROTECT their skill.
        """
        resume_files = [
            (c.resume.storage, c.resume.name) for c in Candidate.objects.exclude(resume="")
        ]
        Application.objects.all().delete()  # cascades to StageChange
        Candidate.objects.all().delete()
        JobOpening.objects.all().delete()  # cascades to JobSkill
        Skill.objects.all().delete()
        # Remove résumé files only once the deletes are committed, so a failed load keeps them.
        transaction.on_commit(lambda: _delete_files_quietly(resume_files))

    def _demo_user(self):
        """The demo staff account (not an admin), with a fresh random password each run."""
        user, _ = get_user_model().objects.get_or_create(username=DEMO_USERNAME)
        password = secrets.token_urlsafe(12)
        user.set_password(password)
        user.is_active = True
        user.first_name, user.last_name = "Demo", "Staff"
        user.save()
        return user, password

    def _load(self, user):
        skills = {name: Skill.objects.create(name=name) for name in SKILLS}

        jobs = {}
        for key, (title, department, location, kind, skill_names, description) in JOBS.items():
            job = JobOpening.objects.create(
                title=title,
                department=department,
                location=location,
                employment_type=kind,
                description=description,
            )
            job.skills.set([skills[name] for name in skill_names])
            jobs[key] = job

        candidates = {}
        for first, last, email, phone, url, notes in CANDIDATES:
            candidates[email] = Candidate.objects.create(
                first_name=first, last_name=last, email=email, phone=phone, url=url, notes=notes
            )

        for email, job_key, source, source_note, moves in APPLICATIONS:
            application = create_application(
                candidate=candidates[email],
                job=jobs[job_key],
                source=source,
                source_note=source_note,
                user=user,
            )
            for move in moves:
                to_stage, reason = move if isinstance(move, tuple) else (move, "")
                application = move_application(
                    application, to_stage=to_stage, user=user, reason=reason
                )

        # Only after their applications are recorded: closed jobs refuse new applications,
        # and archiving is refused while an application is active.
        for key in CLOSED_JOBS:
            close_job(jobs[key])
        for email in ARCHIVED:
            archive_candidate(candidates[email])


def _delete_files_quietly(files):
    """Delete leftover résumé files; one that can't be deleted (e.g. open on Windows) is logged."""
    for storage, name in files:
        try:
            storage.delete(name)
        except OSError:
            logger.warning("Could not delete résumé file %s", name, exc_info=True)
