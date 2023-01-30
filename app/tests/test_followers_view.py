from django.urls import reverse
from django.contrib.auth.models import User

from app.factories import TenderFactory
from app.tests.base import BaseTestCase


class TenderFollowersTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        self.user = user
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

        self.tender = TenderFactory()
        self.url = reverse(
            'tender_followers_view', kwargs={'pk': self.tender.id})

        for i in range(2, 7):
            setattr(self, f'user{i}', User.objects.create(username=f'user{i}'))

    def test_get_followers(self):
        self.tender.followers.add(self.user2, self.user3)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # All users are returned
        self.assertEqual(len(response.json()), User.objects.count())
        follower_ids = [
            int(user["id"]) for user in response.json() if user["is_follower"]
        ]
        # Only two are followers
        self.assertEqual(set(follower_ids), {self.user2.id, self.user3.id})

    def test_add_followers(self):
        self.assertEqual(self.tender.followers.count(), 0)
        payload = {
            'new_followers': [self.user2.id, self.user3.id],
            'unfollowers': []
        }
        response = self.client.post(
            self.url, payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender.followers.count(), 2)

    def test_remove_followers(self):
        self.tender.followers.add(self.user2, self.user3)
        self.assertEqual(self.tender.followers.count(), 2)
        payload = {
            'new_followers': [],
            'unfollowers': [self.user3.id]
        }
        response = self.client.post(
            self.url, payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender.followers.count(), 1)
