import json
import logging

from django.contrib.auth.models import User
from django.urls import reverse

from app.factories import VendorFactory
from app.tests.base import BaseTestCase

from django.utils.http import urlencode


class VendorsListAjaxViewTests(BaseTestCase):
    def setUp(self):
        super(VendorsListAjaxViewTests, self).setUp()
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertTrue(logged_in)

    def test_list_ajax_view_get(self):
        query_kwargs = {
            "start": '0',
            "draw": '1',
            "length": '2',
        }
        vendor1 = VendorFactory(name='vendor1')
        vendor2 = VendorFactory(name='vendor2')
        vendor3 = VendorFactory(name='vendor3')
        vendor4 = VendorFactory(name='vendor4')

        url = '{}?{}'.format(reverse('vendors_list_ajax_view'), urlencode(query_kwargs))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['name'], vendor1.name)
        self.assertEqual(data[1]['name'], vendor2.name)

        query_kwargs.update({"draw": '2', 'start': '2'})
        url = '{}?{}'.format(reverse('vendors_list_ajax_view'), urlencode(query_kwargs))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['name'], vendor3.name)
        self.assertEqual(data[1]['name'], vendor4.name)


