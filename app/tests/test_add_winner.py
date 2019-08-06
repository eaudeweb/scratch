from django.test import TestCase
from app.models import Tender, Winner
from django.core import management


class AddWinnerTestCase(TestCase):
    def setUp(self):
        management.call_command('add_winner', '109206')

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
