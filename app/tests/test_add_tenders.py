from django.test import TestCase
from app.models import Tender, TenderDocument


class AddTenderTestCase(TestCase):
    def setUp(self):
        Tender.objects.create(reference='RFC/TEST/123', url='http://test.com', source='UNGM', unspsc_codes='98765')
        ted_tender = Tender.objects.create(reference='RFC/TEST/1234', url='http://test.org', source='TED',
                                           unspsc_codes='12345')
        TenderDocument.objects.create(tender=ted_tender, download_url='http://test.org/1', name='doc_1')
        TenderDocument.objects.create(tender=ted_tender, download_url='http://test.org/2', name='doc_2')

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

    def test_add_tender_documents(self):
        tender = Tender.objects.get(reference='RFC/TEST/1234')
        documents_list = TenderDocument.objects.filter(tender=tender)
        self.assertEqual(len(documents_list), 2)

        doc_1 = TenderDocument.objects.get(tender=tender, name='doc_1')
        doc_2 = TenderDocument.objects.get(name='doc_2')

        self.assertEqual(doc_1.download_url, 'http://test.org/1')
        self.assertEqual(doc_2.download_url, 'http://test.org/2')

    def test_delete_tender_document(self):
        doc = TenderDocument.objects.get(name='doc_1')
        doc.delete()
        documents = TenderDocument.objects.filter(tender=doc.tender)
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents.first().name, 'doc_2')

    def test_delete_tender_and_documents(self):
        tender = Tender.objects.get(reference='RFC/TEST/1234')
        tender.delete()
        documents = TenderDocument.objects.filter(tender=tender)
        self.assertEqual(len(documents), 0)
