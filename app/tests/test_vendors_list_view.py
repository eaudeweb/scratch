from django.urls import reverse
from django.contrib.auth.models import User

from app.factories import VendorFactory
from app.tests.base import BaseTestCase


class VendorsListViewTests(BaseTestCase):
    def setUp(self):
        super(VendorsListViewTests, self).setUp()
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_list_view_empty_db(self):
        url = reverse('vendors_list_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['vendors'], [])

    def test_list_view_two_vendors(self):
        vendor_1 = VendorFactory(
            name='Vendor1',
            email='email1@email.com',
            contact_name="sample",
            comment="text text"
        )

        vendor_2 = VendorFactory(
            name='Vendor2',
            email='email2@email.com',
            contact_name="sample",
            comment="text text"
        )

        url = reverse('vendors_list_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            list(response.context['vendors']),
            [vendor_1, vendor_2]
        )
        self.assertEqual(response.context['vendors'][0].name, vendor_1.name)
        self.assertEqual(response.context['vendors'][1].name, vendor_2.name)
