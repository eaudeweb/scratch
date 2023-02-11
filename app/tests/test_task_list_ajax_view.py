import json
import logging

from django.contrib.auth.models import User
from django.urls import reverse

from app.factories import TaskFactory
from app.tests.base import BaseTestCase

from django.utils.http import urlencode


class TaskListAjaxViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
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

        task1 = TaskFactory()
        task2 = TaskFactory()
        task3 = TaskFactory()
        task4 = TaskFactory(stopped=None)

        # Tasks are ordered starting from the newest by default
        ordered = [task4, task3, task2, task1]

        url = '{}?{}'.format(
            reverse('task_list_ajax_view'), urlencode(query_kwargs))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['id'], ordered[0].id)
        self.assertEqual(data[1]['id'], ordered[1].id)

        query_kwargs.update({"draw": '2', 'start': '2'})
        url = '{}?{}'.format(
            reverse('task_list_ajax_view'), urlencode(query_kwargs))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['id'], ordered[2].id)
        self.assertEqual(data[1]['id'], ordered[3].id)
