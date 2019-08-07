from django.test import TestCase
from app.models import Tender, Winner
from django.utils import timezone
from datetime import datetime


class AddWinnerTestCase(TestCase):
    def setUp(self):
        tender = Tender.objects.create(
            title="test_title",
            reference="RFC/TEST/123",
            url="http://test.com",
            source="UNGM",
            unspsc_codes="98765",
        )
        Winner.objects.create(
            vendor="test_vendor",
            currency="USD",
            award_date=datetime.now(timezone.utc),
            tender=tender
        )

    def test_add_winner(self):
        tenders = Tender.objects.all()
        winners = Winner.objects.all()

        self.assertEqual(len(winners), 1)
        self.assertEqual(len(tenders), 1)
        self.assertEqual(winners[0].tender.reference, tenders[0].reference)

    def test_remove_winner(self):
        tenders = Tender.objects.all()
        Tender.objects.get(reference=tenders[0].reference).delete()

        tenders = Tender.objects.all()
        winners = Winner.objects.all()

        self.assertEqual(len(winners), 0)
        self.assertEqual(len(tenders), 0)
