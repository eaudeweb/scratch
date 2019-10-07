from django.contrib.auth.models import User
from django.urls import reverse
from django.core import management
from elasticsearch import RequestError

from app.factories import KeywordFactory, TenderFactory
from app.models import UNSPSCCode, Tender
from app.parsers.ungm import UNGMWorker
from app.tests.base import BaseTestCase


class SearchTestCase(BaseTestCase):
    def setUp(self):
        super(SearchTestCase, self).setUp()

        try:
            management.call_command("search_index", "--create")
        except RequestError:
            pass

        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

        self.keyword = KeywordFactory()
        self.tender_1 = TenderFactory(title='Tender_1')
        self.tender_2 = TenderFactory(title='Tender_2')

    def test_tender_search(self):
        url = reverse('search_results', kwargs={'pk': 'Tender_1'})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<mark>Tender_1</mark>')

    def test_tender_document_search(self):
        self.worker = UNGMWorker()
        self.url = 'wwww.parser_test.com'
        self.unspsc_codes = UNSPSCCode.objects.all()

        with open('app/tests/parser_files/ungm_notice_es_search.html', 'r') as f:
            html_string = f.read()

            tender = self.worker.parse_ungm_notice(html_string, self.url,
                                                   self.unspsc_codes)

            self.worker.update_ungm_tenders([tender])

            url = reverse('search_results', kwargs={'pk': 'Courtney'})
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Software Development and Maintenance of NET-VISA, on a Call-off Basis")
