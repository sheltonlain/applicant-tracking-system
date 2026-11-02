import factory

from jobs.models import JobOpening


class JobOpeningFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobOpening

    title = factory.Sequence(lambda n: f"Job {n}")
    description = "Job description."
    department = "Engineering"
    location = "Remote"
    employment_type = JobOpening.EmploymentType.FULL_TIME
