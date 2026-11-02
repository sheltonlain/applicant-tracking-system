import factory

from applications.models import Application, StageChange
from candidates.tests.factories import CandidateFactory
from conftest import UserFactory
from jobs.tests.factories import JobOpeningFactory


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application

    candidate = factory.SubFactory(CandidateFactory)
    job = factory.SubFactory(JobOpeningFactory)
    source = Application.Source.COMPANY_WEBSITE


class StageChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StageChange

    application = factory.SubFactory(ApplicationFactory)
    from_stage = ""
    to_stage = Application.Stage.APPLIED
    user = factory.SubFactory(UserFactory)
