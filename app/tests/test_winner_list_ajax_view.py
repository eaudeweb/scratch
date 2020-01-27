import json

from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.http import urlencode

from app.factories import AwardFactory, TenderFactory, VendorFactory
from app.tests.base import BaseTestCase


class AwardsListAjaxViewTests(BaseTestCase):
    def setUp(self):
        super(AwardsListAjaxViewTests, self).setUp()
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

        new_award1 = AwardFactory()
        new_award2 = AwardFactory()
        new_award3 = AwardFactory()
        new_award4 = AwardFactory()
        new_award1.vendors.add(vendor1)
        new_award2.vendors.add(vendor1)
        new_award3.vendors.add(vendor2)
        new_award4.vendors.add(vendor2)

        url = '{}?{}'.format(reverse('contract_awards_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        data = json.loads(response.content)['data']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['title'], new_award1.tender.title)
        self.assertEqual(data[0]['source'], new_award1.tender.source)
        self.assertEqual(data[0]['organization'], new_award1.tender.organization)
        self.assertEqual(data[0]['value'], str(new_award1.value))
        self.assertEqual(data[0]['currency'], new_award1.currency)

        self.assertEqual(data[1]['title'], new_award2.tender.title)
        self.assertEqual(data[1]['source'], new_award2.tender.source)
        self.assertEqual(data[1]['organization'], new_award2.tender.organization)
        self.assertEqual(data[1]['value'], str(new_award2.value))
        self.assertEqual(data[1]['currency'], new_award2.currency)

        query_kwargs.update({"draw": '2', 'start': '2'})
        url = '{}?{}'.format(reverse('contract_awards_list_ajax_view'), urlencode(query_kwargs))
        response = self.client.get(url)
        data = json.loads(response.content)['data']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['title'], new_award3.tender.title)
        self.assertEqual(data[0]['source'], new_award3.tender.source)
        self.assertEqual(data[0]['organization'], new_award3.tender.organization)
        self.assertEqual(data[0]['value'], str(new_award3.value))
        self.assertEqual(data[0]['currency'], new_award3.currency)

        self.assertEqual(data[1]['title'], new_award4.tender.title)
        self.assertEqual(data[1]['source'], new_award4.tender.source)
        self.assertEqual(data[1]['organization'], new_award4.tender.organization)
        self.assertEqual(data[1]['value'], str(new_award4.value))
        self.assertEqual(data[1]['currency'], new_award4.currency)

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
        award_meeting_filters = AwardFactory(tender=tender)
        award_meeting_filters.vendors.add(vendor1)
        award_not_meeting_filters =  AwardFactory()
        award_not_meeting_filters.vendors.add(vendor2)
        url =  '{}?{}'.format(reverse('contract_awards_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[1]['title'], award_meeting_filters.tender.title)
        self.assertEqual(data[1]['source'], award_meeting_filters.tender.source)
        self.assertEqual(data[1]['organization'], award_meeting_filters.tender.organization)
        self.assertEqual(data[1]['value'], award_meeting_filters.value)
        self.assertEqual(data[1]['currency'], award_meeting_filters.currency)

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
        award1 = AwardFactory(tender=tender1)
        award2 = AwardFactory(tender=tender2)
        award1.vendors.add(vendor1)
        award2.vendors.add(vendor2)

        url = '{}?{}'.format(reverse('contract_awards_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['title'], award2.tender.title)
        self.assertEqual(data[0]['source'], award2.tender.source)
        self.assertEqual(data[0]['organization'], award2.tender.organization)
        self.assertEqual(data[0]['value'], str(award2.value))
        self.assertEqual(data[0]['currency'], award2.currency)
