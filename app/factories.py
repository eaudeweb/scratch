import factory
from .models import Tender, Winner, Notification
from datetime import datetime
from django.utils import timezone


class TenderFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tender

    reference = factory.sequence(lambda n: "RFC/TEST/%s" % n)
    organization = 'UNOPS'
    source = 'UNGM'
    unspsc_codes = '98765'
    url = "http://test.com"
    published = datetime.now(timezone.utc)
    deadline = datetime.now(timezone.utc)


class WinnerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Winner

    currency = "USD"
    award_date = datetime.now(timezone.utc)
    tender = factory.SubFactory(TenderFactory)


class NotificationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Notification
