from app.models import Tender, Winner, Vendor
from app.factories import TenderFactory, WinnerFactory, VendorFactory
from app.tests.base import BaseTestCase


class AddWinnerTestCase(BaseTestCase):
    def setUp(self):
        super(AddWinnerTestCase, self).setUp()

        self.expected_vendor_name = "test_vendor"

        tender = TenderFactory(title="test_title")
        vendor = VendorFactory(name=self.expected_vendor_name)
        WinnerFactory(vendor=vendor, tender=tender)

    def test_add_winner(self):
        tenders = Tender.objects.all()
        winners = Winner.objects.all()

        self.assertEqual(len(winners), 1)
        self.assertEqual(len(tenders), 1)
        self.assertEqual(winners[0].vendor.name, self.expected_vendor_name)
        self.assertEqual(winners[0].tender.reference, tenders[0].reference)

    def test_remove_winner(self):
        tenders = Tender.objects.all()
        Tender.objects.get(reference=tenders[0].reference).delete()

        tenders = Tender.objects.all()
        winners = Winner.objects.all()

        self.assertEqual(len(winners), 0)
        self.assertEqual(len(tenders), 0)
