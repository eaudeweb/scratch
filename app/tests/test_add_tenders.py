from django.test import TestCase
from app.models import Tender


class AddTenderTestCase(TestCase):
    def setUp(self):
        Tender.objects.create(reference='RFC/TEST/123', url='http://test.com', source='UNGM', unspsc_codes='98765')
        Tender.objects.create(reference='RFC/TEST/1234', url='http://test.org', source='TED', unspsc_codes='12345')

    def test_add_tenders(self):
        t1 = Tender.objects.get(reference='RFC/TEST/123')
        t2 = Tender.objects.get(url='http://test.org')
        self.assertEqual(t1.url, 'http://test.com')
        self.assertEqual(t2.reference, 'RFC/TEST/1234')

    def test_remove_tenders(self):
        Tender.objects.get(reference='RFC/TEST/123').delete()

        tenders = Tender.objects.all()
        self.assertEqual(len(tenders), 1)
        self.assertEqual(tenders[0].reference, 'RFC/TEST/1234')
