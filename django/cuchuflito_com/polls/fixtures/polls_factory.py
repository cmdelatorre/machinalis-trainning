import factory
from polls.models import Poll, Choice
from django.contrib.auth.models import User

DEFAULT_PASSWORD = "123"

class UserFactory(factory.Factory):
    FACTORY_FOR = User
    username = factory.Sequence(lambda n: 'user {0}'.format(n))
    password = DEFAULT_PASSWORD

class PollFactory(factory.Factory):
    FACTORY_FOR = Poll

    question = factory.Sequence(lambda n: 'Question {0}'.format(n))
    created_by = factory.SubFactory(UserFactory)


class ChoiceFactory(factory.Factory):
    FACTORY_FOR = Choice

    poll = factory.SubFactory(PollFactory)
    choice = factory.Sequence(lambda n: 'Choice {0}'.format(n))