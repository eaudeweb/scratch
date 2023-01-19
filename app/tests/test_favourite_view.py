from django.urls import reverse
from django.contrib.auth.models import User

from app.factories import TenderFactory
from app.models import Tender
from app.tests.base import BaseTestCase


class TendersFavouriteTests(BaseTestCase):
    def setUp(self):
        super(TendersFavouriteTests, self).setUp()
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        self.user = user
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_add_to_favourites(self):
        new_tender = TenderFactory()
        url = reverse('tender_favourite_view', kwargs={'pk': new_tender.id})
        response = self.client.post(url, {'favourite': 'true'})
        self.assertEqual(response.status_code, 200)
        tender_added = Tender.objects.get(reference=new_tender.reference)
        self.assertEqual(tender_added.followers.count(), 1)

    def test_remove_from_favourites(self):
        new_tender = TenderFactory()
        new_tender.followers.add(self.user)
        self.assertEqual(new_tender.followers.count(), 1)
        url = reverse('tender_favourite_view', kwargs={'pk': new_tender.id})
        response = self.client.post(url, {'favourite': 'false'})
        self.assertEqual(response.status_code, 200)
        tender_added = Tender.objects.get(reference=new_tender.reference)
        self.assertEqual(new_tender.followers.count(), 0)
