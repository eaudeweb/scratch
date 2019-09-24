from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from app.factories import TenderFactory, KeywordFactory


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
        tender_1 = TenderFactory(title='Tender1')
        tender_2 = TenderFactory(title='Tender2', source='TED')
        url = reverse('tenders_list_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            list(response.context['tenders']),
            ['<Tender: Tender1>', '<Tender: Tender2>']
        )
        self.assertEqual(response.context['tenders'][0].reference, tender_1.reference)
        self.assertEqual(response.context['tenders'][1].source, tender_2.source)

    def test_list_view_has_keywords(self):
        keyword = KeywordFactory()
        tender = TenderFactory(title='Tender1 python')
        url = reverse('tenders_list_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            list(response.context['tenders']),
            ['<Tender: Tender1 python>']
        )
        self.assertEqual(response.context['tenders'][0].reference, tender.reference)
        self.assertContains(response, 'Tender1 <mark>python</mark>')
