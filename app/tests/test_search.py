import os

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management import call_command
from django.urls import reverse

from app.factories import KeywordFactory, TenderFactory, TenderDocumentFactory
from app.tests.base import BaseTestCase


class SearchTestCase(BaseTestCase):
    def setUp(self):
        super(SearchTestCase, self).setUp()

        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

        self.keyword = KeywordFactory()
        self.tender_1 = TenderFactory(title='Tender_1')
        self.tender_2 = TenderFactory(title='Tender_2')
        self.tender_document = TenderDocumentFactory()
        self.tender_document.tender = self.tender_1

        with open('app/tests/parser_files/Test_search.pdf', 'rb') as g:
            self.tender_document.document.save(self.tender_document.name, File(g), save=True)

        with open(os.devnull, 'w') as f:
            call_command('search_index', '--rebuild', '-f', stdout=f)

    def test_tender_search(self):
        url = reverse('search_results', kwargs={'pk': 'Tender_1'})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<mark>Tender_1</mark>')

    def test_tender_document_search(self):
        url = reverse('search_results', kwargs={'pk': 'Test'})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tender_1')
