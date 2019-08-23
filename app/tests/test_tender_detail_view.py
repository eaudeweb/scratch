from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from app.factories import TenderFactory

class TendersDetailViewTests(TestCase):
    def setUp(self):
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_detail_view_no_tender(self):
        url = reverse('tender_detail_view', kwargs={'pk': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_one_tender(self):
        new_tender = TenderFactory()
        url = reverse('tender_detail_view', kwargs={'pk': new_tender.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_tender.title)
        self.assertContains(response, new_tender.reference)
