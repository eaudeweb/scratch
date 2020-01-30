from app.models import Tender, Award
from app.factories import TenderFactory, AwardFactory, VendorFactory
from app.tests.base import BaseTestCase


class AddAwardTestCase(BaseTestCase):
    def setUp(self):
        super(AddAwardTestCase, self).setUp()

        self.expected_vendor_name = 'test_vendor'

        tender = TenderFactory(title='test_title')
        vendor = VendorFactory(name=self.expected_vendor_name)
        award = AwardFactory(tender=tender)
        award.vendors.add(vendor)
        award.save()

    def test_add_award(self):
        tenders = Tender.objects.all()
        awards = Award.objects.all()

        self.assertEqual(len(awards), 1)
        self.assertEqual(len(tenders), 1)
        self.assertEqual(awards[0].vendors.first().name, self.expected_vendor_name)
        self.assertEqual(awards[0].tender.reference, tenders[0].reference)

    def test_remove_award(self):
        tenders = Tender.objects.all()
        Tender.objects.get(reference=tenders[0].reference).delete()

        tenders = Tender.objects.all()
        awards = Award.objects.all()

        self.assertEqual(len(awards), 0)
        self.assertEqual(len(tenders), 0)
