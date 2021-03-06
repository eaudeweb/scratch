import json

from django.urls import reverse
from django.contrib.auth.models import User

from app.factories import TenderFactory, KeywordFactory
from app.tests.base import BaseTestCase

from django.utils.http import urlencode


class TendersListAjaxViewTests(BaseTestCase):
    def setUp(self):
        super(TendersListAjaxViewTests, self).setUp()
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
        KeywordFactory()
        new_tender1 = TenderFactory(title='Tender1 python')
        new_tender2 = TenderFactory()
        new_tender3 = TenderFactory()
        new_tender4 = TenderFactory()

        url = '{}?{}'.format(reverse('tenders_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context), 2)
        data = json.loads(response.content)['data']

        self.assertEqual(response.context[0]['tender'], new_tender1)
        self.assertEqual(data[0]['title'], 'Tender1 <mark>python</mark>')
        self.assertEqual(response.context[1]['tender'], new_tender2)

        query_kwargs.update({"draw": '2', 'start': '2'})
        url = '{}?{}'.format(reverse('tenders_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context), 2)
        self.assertEqual(response.context[0]['tender'], new_tender3)
        self.assertEqual(response.context[1]['tender'], new_tender4)

    def test_list_ajax_view_filters(self):
        query_kwargs = {
            "start": '0',
            "draw": '1', 
            "length": '10',
            "source": "TED",
            "organization": "Test organization",
            "favourite": "True",
            "notice_type": "Aditional information"
        }
        tender_meeting_filters = TenderFactory(
            title="Test title", source="TED", organization="Test organization",
            favourite=True, notice_type="Aditional information"
        )
        TenderFactory()
        url = '{}?{}'.format(reverse('tenders_list_ajax_view'),  urlencode(query_kwargs))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context.dicts), 2)
        self.assertEqual(response.context.dicts[1]['tender'], tender_meeting_filters)

    def test_list_ajax_view_filters(self):
        query_kwargs = {
            "start": '0',
            "draw": '1',
            "length": '10',
            "order[0][column]": "1",
            "order[0][dir]": "desc",
        }

        TenderFactory(source="TED")
        tender2 = TenderFactory(source="UNGM")

        url = '{}?{}'.format(reverse('tenders_list_ajax_view'), urlencode(query_kwargs))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context), 2)
        self.assertEqual(response.context[0]['tender'], tender2)
