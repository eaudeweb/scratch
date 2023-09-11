import os
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse

from app.factories import KeywordFactory, TenderFactory
from app.models import UNSPSCCode, Tender
from app.parsers.ungm import UNGMWorker
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

        with open(os.devnull, 'w') as f:
            call_command('search_index', '--rebuild', '-f', stdout=f)

    def test_tender_search(self):
        url = reverse('search_results', kwargs={'pk': 'Tender_1'})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<mark>Tender_1</mark>')

    @patch('app.parsers.ungm.requests')
    def test_tender_document_search(self, mock_requests):
        worker = UNGMWorker()
        url = 'wwww.parser_test.com'
        unspsc_codes = UNSPSCCode.objects.all()
        with open('app/tests/parser_files/RFP2019-0148-RAHMAN.pdf', 'rb') as g:

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_content.return_value = [g.read()]

        mock_requests.get.return_value = mock_response

        with open('app/tests/parser_files/ungm_notice_es_search.html', 'r') as f:
            html_string = f.read()
            tender = worker.parse_ungm_notice(html_string, url, unspsc_codes)
            worker.update_ungm_tenders([tender])
            with open(os.devnull, 'w') as g:
                call_command('search_index', '--rebuild', '-f', stdout=g)
            url = reverse('search_results', kwargs={'pk': 'Courtney'})
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                'Software Development and Maintenance of NET-VISA, on a Call-off Basis',
            )
