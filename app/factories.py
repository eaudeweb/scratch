import factory
from .models import (
    Tender, Award, TenderDocument, CPVCode,
    TedCountry, UNSPSCCode, Keyword, Vendor, Tag, Profile
)
from datetime import datetime
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.utils import timezone

User = get_user_model()


@factory.django.mute_signals(post_save)
class ProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = Profile
    
    notify = True
    user = factory.SubFactory("app.factories.UserFactory")

@factory.django.mute_signals(post_save)
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.sequence(lambda n: f"test{n}")
    email = factory.sequence(lambda n: f"test{n}@test.test")
    profile = factory.RelatedFactory(ProfileFactory, factory_related_name='user')



class TenderFactory(factory.DjangoModelFactory):
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


class TenderDocumentFactory(factory.DjangoModelFactory):
    class Meta:
        model = TenderDocument

    name = factory.sequence(lambda n: 'Doc_%s' % n)
    download_url = factory.sequence(lambda n: "http://test.org/%s" % n)
    tender = factory.SubFactory(TenderFactory)


class AwardFactory(factory.DjangoModelFactory):
    class Meta:
        model = Award

    value = 10
    currency = "USD"
    award_date = datetime.now(timezone.utc)
    renewal_date = datetime.now(timezone.utc)
    tender = factory.SubFactory(TenderFactory)


class VendorFactory(factory.DjangoModelFactory):
    class Meta:
        model = Vendor

    name = "test"
    email = "test@email.com"
    contact_name = "Test"
    comment = "Test test"


class CPVCodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = CPVCode


class TedCountryFactory(factory.DjangoModelFactory):
    class Meta:
        model = TedCountry


class UNSPCCodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = UNSPSCCode


class KeywordFactory(factory.DjangoModelFactory):
    class Meta:
        model = Keyword

    value = 'python'

class TagsFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tag

    name = 'django'
