from django.test import TestCase
from app.models import Tender, Winner
from app.factories import TenderFactory, WinnerFactory


class AddWinnerTestCase(TestCase):
    def setUp(self):
        tender = TenderFactory(title="test_title")
        WinnerFactory(vendor="test_vendor", tender=tender)

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
