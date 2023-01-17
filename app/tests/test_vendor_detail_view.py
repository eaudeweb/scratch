from django.contrib.auth.models import User
from django.urls import reverse

from app.factories import VendorFactory
from app.tests.base import BaseTestCase


class VendorDetailViewTests(BaseTestCase):
    def setUp(self):
        super(VendorDetailViewTests, self).setUp()
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_detail_view_no_tender(self):
        url = reverse('vendor_detail_view', kwargs={'pk': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_one_tender(self):
        vendor = VendorFactory()
        url = reverse('vendor_detail_view', kwargs={'pk': vendor.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["vendor"].name, vendor.name)
        self.assertEqual(response.context["vendor"].email, vendor.email)
        self.assertEqual(response.context["vendor"].comment, vendor.comment)
        self.assertEqual(response.context["vendor"].contact_name, vendor.contact_name)