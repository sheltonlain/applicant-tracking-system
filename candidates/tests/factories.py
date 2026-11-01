import factory

from candidates.models import Candidate


class CandidateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Candidate

    first_name = factory.Sequence(lambda n: f"First{n}")
    last_name = factory.Sequence(lambda n: f"Last{n}")
    email = factory.Sequence(lambda n: f"candidate{n}@example.com")
