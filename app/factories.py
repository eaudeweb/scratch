import factory
import factory.fuzzy
import random
from faker import Faker
from .models import (
    Tender, Award, TenderDocument, CPVCode,
    TedCountry, UNSPSCCode, Keyword, Vendor, Tag, Profile, Task
)
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django_q.humanhash import uuid
from django.utils import timezone

User = get_user_model()

fake = Faker()


@factory.django.mute_signals(post_save)
class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    notify = True
    user = factory.SubFactory("app.factories.UserFactory")


@factory.django.mute_signals(post_save)
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.sequence(lambda n: f"test{n}")
    email = factory.sequence(lambda n: f"test{n}@test.test")
    profile = factory.RelatedFactory(
        ProfileFactory, factory_related_name='user')


class TenderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tender

    reference = factory.sequence(lambda n: "RFC/TEST/%s" % n)
    title = factory.sequence(lambda n: "Tender%s" % n)
    organization = 'UNOPS'
    source = 'UNGM'
    description = 'test'
    unspsc_codes = '98765'
    url = factory.sequence(lambda n: "http://test.com/%s" % n)
    published = datetime.now(timezone.utc)
    deadline = datetime.now(timezone.utc)


class TenderDocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TenderDocument

    name = factory.sequence(lambda n: 'Doc_%s' % n)
    download_url = factory.sequence(lambda n: "http://test.org/%s" % n)
    tender = factory.SubFactory(TenderFactory)


class AwardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Award

    value = 10
    currency = "USD"
    award_date = datetime.now(timezone.utc)
    renewal_date = datetime.now(timezone.utc)
    tender = factory.SubFactory(TenderFactory)


class VendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vendor

    name = "test"
    email = "test@email.com"
    contact_name = "Test"
    comment = "Test test"


class CPVCodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CPVCode


class TedCountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TedCountry


class UNSPCCodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UNSPSCCode


class KeywordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Keyword

    value = 'python'


class TagsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = 'django'


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    id = factory.LazyFunction(lambda: uuid()[1])
    args = factory.fuzzy.FuzzyChoice(settings.RUNNABLE_COMMANDS)
    kwargs = factory.fuzzy.FuzzyChoice(
        ["digest: True", "days_ago: 1", "given_date: 2022-12-21"]
    )
    started = factory.LazyAttributeSequence(
        lambda obj, n: timezone.now() + timedelta(minutes=n+1))
    stopped = factory.LazyAttribute(
        lambda obj: obj.started + timedelta(minutes=random.randint(1, 9)))
    status = factory.fuzzy.FuzzyChoice(["processing", "success", "error"])

    @factory.lazy_attribute
    def stopped(self):
        random_int = random.randint(-3, 9)
        if random_int > 0:
            return self.started + timedelta(minutes=random_int)
        return None

    @factory.lazy_attribute
    def status(self):
        if self.stopped:
            return random.choice(["success", "error"])
        return "processing"

    @factory.lazy_attribute
    def output(self):
        random_int = random.randint(-3, 9)
        if random_int > 0 and self.stopped:
            return fake.paragraph(
                nb_sentences=random_int, variable_nb_sentences=False
            )
        return ""
