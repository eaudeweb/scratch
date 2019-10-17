import json

from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.http import urlencode

from app.factories import WinnerFactory, TenderFactory, VendorFactory
from app.tests.base import BaseTestCase


class WinnersListAjaxViewTests(BaseTestCase):
    def setUp(self):
        super(WinnersListAjaxViewTests, self).setUp()
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_list_ajax_view_get(self):
        query_kwargs = {
            "start": '0',
            "draw": '1', 
            "length": '2',
        }
        vendor1 = VendorFactory()
        vendor2 = VendorFactory()

        new_winner1 = WinnerFactory()
        new_winner2 = WinnerFactory()
        new_winner3 = WinnerFactory()
        new_winner4 = WinnerFactory()
        new_winner1.vendors.add(vendor1)
        new_winner2.vendors.add(vendor1)
        new_winner3.vendors.add(vendor2)
        new_winner4.vendors.add(vendor2)

        url = '{}?{}'.format(reverse('contract_awards_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        data = json.loads(response.content)['data']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['title'], new_winner1.tender.title)
        self.assertEqual(data[0]['source'], new_winner1.tender.source)
        self.assertEqual(data[0]['organization'], new_winner1.tender.organization)
        self.assertEqual(data[0]['value'], str(new_winner1.value))
        self.assertEqual(data[0]['currency'], new_winner1.currency)

        self.assertEqual(data[1]['title'], new_winner2.tender.title)
        self.assertEqual(data[1]['source'], new_winner2.tender.source)
        self.assertEqual(data[1]['organization'], new_winner2.tender.organization)
        self.assertEqual(data[1]['value'], str(new_winner2.value))
        self.assertEqual(data[1]['currency'], new_winner2.currency)

        query_kwargs.update({"draw": '2', 'start': '2'})
        url = '{}?{}'.format(reverse('contract_awards_list_ajax_view'), urlencode(query_kwargs))
        response = self.client.get(url)
        data = json.loads(response.content)['data']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['title'], new_winner3.tender.title)
        self.assertEqual(data[0]['source'], new_winner3.tender.source)
        self.assertEqual(data[0]['organization'], new_winner3.tender.organization)
        self.assertEqual(data[0]['value'], str(new_winner3.value))
        self.assertEqual(data[0]['currency'], new_winner3.currency)

        self.assertEqual(data[1]['title'], new_winner4.tender.title)
        self.assertEqual(data[1]['source'], new_winner4.tender.source)
        self.assertEqual(data[1]['organization'], new_winner4.tender.organization)
        self.assertEqual(data[1]['value'], str(new_winner4.value))
        self.assertEqual(data[1]['currency'], new_winner4.currency)

    def test_list_ajax_view_filters(self):
        query_kwargs = {
            "start": '0',
            "draw": '1', 
            "length": '10',
            "source": "TED",
            "organization": "Test organization",
            "value": "2",
        }
        tender = TenderFactory(
            source="TED", organization="Test organization",
            value="45000"
        )
        vendor1 = VendorFactory()
        vendor2 = VendorFactory()
        winner_meeting_filters = WinnerFactory(tender=tender)
        winner_meeting_filters.vendors.add(vendor1)
        winner_not_meeting_filters =  WinnerFactory()
        winner_not_meeting_filters.vendors.add(vendor2)
        url =  '{}?{}'.format(reverse('contract_awards_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[1]['title'], winner_meeting_filters.tender.title)
        self.assertEqual(data[1]['source'], winner_meeting_filters.tender.source)
        self.assertEqual(data[1]['organization'], winner_meeting_filters.tender.organization)
        self.assertEqual(data[1]['value'], winner_meeting_filters.value)
        self.assertEqual(data[1]['currency'], winner_meeting_filters.currency)

    def test_list_ajax_view_filters(self):
        query_kwargs = {
            "start": '0',
            "draw": '1',
            "length": '10',
            "order[0][column]": "1",
            "order[0][dir]": "desc",
        }

        tender1 = TenderFactory(source="TED")
        tender2 = TenderFactory(source="UNGM")
        vendor1 = VendorFactory()
        vendor2 = VendorFactory()
        winner1 = WinnerFactory(tender=tender1)
        winner2 = WinnerFactory(tender=tender2)
        winner1.vendors.add(vendor1)
        winner2.vendors.add(vendor2)

        url = '{}?{}'.format(reverse('contract_awards_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['title'], winner2.tender.title)
        self.assertEqual(data[0]['source'], winner2.tender.source)
        self.assertEqual(data[0]['organization'], winner2.tender.organization)
        self.assertEqual(data[0]['value'], str(winner2.value))
        self.assertEqual(data[0]['currency'], winner2.currency)
