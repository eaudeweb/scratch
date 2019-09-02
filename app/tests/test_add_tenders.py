from django.test import TestCase
from app.models import Tender, TenderDocument
from app.factories import TenderFactory, TenderDocumentFactory


class AddTenderTestCase(TestCase):
    def setUp(self):
        self.tender_1 = TenderFactory(title='Tender_1 python')
        self.tender_2 = TenderFactory(title='Tender_2', source='TED')
        self.doc_1 = TenderDocumentFactory(tender=self.tender_2)
        self.doc_2 = TenderDocumentFactory(tender=self.tender_2)

    def test_add_tenders(self):
        t1 = Tender.objects.get(reference=self.tender_1.reference)
        t2 = Tender.objects.get(url=self.tender_2.url)
        self.assertEqual(t1.url, self.tender_1.url)
        self.assertEqual(t2.reference, self.tender_2.reference)

    def test_add_tenders_with_keywords(self):
        t1 = Tender.objects.get(reference=self.tender_1.reference)
        t2 = Tender.objects.get(reference=self.tender_2.reference)
        self.assertEqual(t1.has_keywords, True)
        self.assertEqual(t2.has_keywords, False)

    def test_remove_tenders(self):
        Tender.objects.get(reference=self.tender_1.reference).delete()
        tenders = Tender.objects.all()
        self.assertEqual(len(tenders), 1)
        self.assertEqual(tenders[0].reference, self.tender_2.reference)

    def test_add_tender_documents(self):
        tender = Tender.objects.get(reference=self.tender_2.reference)
        documents_list = TenderDocument.objects.filter(tender=tender)
        self.assertEqual(len(documents_list), 2)

        doc_1 = TenderDocument.objects.get(tender=tender, name=self.doc_1.name)
        doc_2 = TenderDocument.objects.get(name=self.doc_2.name)

        self.assertEqual(doc_1.download_url, self.doc_1.download_url)
        self.assertEqual(doc_2.download_url, self.doc_2.download_url)

    def test_delete_tender_document(self):
        doc = TenderDocument.objects.get(name=self.doc_1.name)
        doc.delete()
        documents = TenderDocument.objects.filter(tender=doc.tender)
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents.first().name, self.doc_2.name)

    def test_delete_tender_and_documents(self):
        tender = Tender.objects.get(reference=self.tender_2.reference)
        tender.delete()
        documents = TenderDocument.objects.filter(tender=tender)
        self.assertEqual(len(documents), 0)
