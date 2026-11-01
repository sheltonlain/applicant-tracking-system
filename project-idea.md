This is a new Django application named Applicant Tracking System (ATS). It is an internal application manager that will allow staff to classify job applications as different lifecycle stages. 


We will build this application using the following tech stack: 

Python
Django
SQLite
uv
Tailwind CSS with DaisyUI using django-tailwind-cli
HTMX
Ruff
pytest


Here are the requirements for ATS:

This is an internal hiring system. It will be used by employees involved in the hiring process. Candidates will not log in to the system.

Staff need to keep track of candidates and their basic information. Candidates may come from the company website, job boards, referrals, or other outside sources.

Staff need to create and edit job openings. A job opening can be open or closed.

Staff need to record when a candidate applies for a job opening. A candidate may apply for several different jobs, but should not have more than one application for the same opening.

Applications move through a defined hiring process. The system must include these stages: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, and Withdrawn.

Staff need an easy way to see where applicants are in the hiring process and move them from one stage to another. Moving an applicant should not require reloading the entire page.

The system needs to keep track of the skills associated with each job opening. The same skill may apply to many different openings.

We need to decide how candidate records should be managed over time. For example, we have not decided when a candidate should be edited, archived, deactivated, or removed.

We need to decide what happens when a job opening closes. Existing applications may still be in progress, and an opening may or may not be allowed to reopen.

