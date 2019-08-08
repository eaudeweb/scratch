from django.test import TestCase
from django.urls import reverse
from app.models import Tender
from django.contrib.auth.models import User
from app.factories import TenderFactory


class TendersFavouriteTests(TestCase):
    def setUp(self):
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_add_to_favourites(self):
        new_tender = TenderFactory(favourite=False)
        url = reverse('tender_favourite_view', kwargs={'pk': new_tender.id})
        response = self.client.post(url, {'favourite': 'true'})
        self.assertEqual(response.status_code, 200)
        tender_added = Tender.objects.get(reference=new_tender.reference)
        self.assertEqual(tender_added.favourite, True)
        tender_added.delete()

    def test_remove_from_favourites(self):
        new_tender = TenderFactory(favourite=True)
        url = reverse('tender_favourite_view', kwargs={'pk': new_tender.id})
        response = self.client.post(url, {'favourite': 'false'})
        self.assertEqual(response.status_code, 200)
        tender_added = Tender.objects.get(reference=new_tender.reference)
        self.assertEqual(tender_added.favourite, False)
        tender_added.delete()
