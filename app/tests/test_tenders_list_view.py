from django.test import TestCase
from django.urls import reverse

from app.models import Tender, TenderDocument
from django.contrib.auth.models import User


def create_tenders():
    Tender.objects.create(
        title='Tender1',
        reference='RFC/TEST/12345',
        url='http://test.com',
        source='UNGM',
        unspsc_codes='1234'
    )
    ted_tender = Tender.objects.create(
        title='Tender2',
        reference='RFC/TEST/123456',
        url='http://test.org',
        source='TED',
        unspsc_codes='12345'
    )
    TenderDocument.objects.create(tender=ted_tender, download_url='http://test.org/1', name='doc_1')
    TenderDocument.objects.create(tender=ted_tender, download_url='http://test.org/2', name='doc_2')


class TendersListViewTests(TestCase):
    def setUp(self):
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_list_view_empty_db(self):
        url = reverse('tenders_list_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['tenders'], [])

    def test_list_view_two_tenders(self):
        create_tenders()
        url = reverse('tenders_list_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            list(response.context['tenders']),
            ['<Tender: Tender1>', '<Tender: Tender2>']
        )
        self.assertEqual(response.context['tenders'][0].reference, 'RFC/TEST/12345')
        self.assertEqual(response.context['tenders'][1].source, 'TED')