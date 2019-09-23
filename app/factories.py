import factory
from .models import Tender, Winner, Notification, TenderDocument, CPVCode, TedCountry, Keyword
from datetime import datetime
from django.utils import timezone


class TenderFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tender

    reference = factory.sequence(lambda n: "RFC/TEST/%s" % n)
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


class WinnerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Winner

    currency = "USD"
    award_date = datetime.now(timezone.utc)
    tender = factory.SubFactory(TenderFactory)


class NotificationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Notification

    email = factory.sequence(lambda n: "test%s@test.test" % n)


class CPVCodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = CPVCode


class TedCountryFactory(factory.DjangoModelFactory):
    class Meta:
        model = TedCountry


class KeywordFactory(factory.DjangoModelFactory):
    class Meta:
        model = Keyword

    value = 'python'
