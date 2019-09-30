from django.urls import reverse
from app.models import Tender
from django.contrib.auth.models import User
from app.factories import TenderFactory
from app.tests.base import BaseTestCase


class TendersFavouriteTests(BaseTestCase):
    def setUp(self):
        super(TendersFavouriteTests, self).setUp()
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_delete_tender(self):
        new_tender = TenderFactory()
        url = reverse('tender_delete_view', kwargs={'pk': new_tender.id})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        tender_deleted = Tender.objects.filter(reference=new_tender.reference)
        self.assertQuerysetEqual(tender_deleted, [])
