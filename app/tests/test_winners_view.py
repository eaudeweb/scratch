from datetime import timedelta, date

from django.contrib.auth.models import User
from django.urls import reverse

from app.factories import TenderFactory, WinnerFactory, VendorFactory
from app.tests.base import BaseTestCase


class WinnersViewTest(BaseTestCase):
    def setUp(self):
        super(WinnersViewTest, self).setUp()
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()

        vendor = VendorFactory(name="test_vendor")
        self.tender = TenderFactory(title="test_title")
        self.winner = WinnerFactory(vendor=vendor, tender=self.tender)

    def test_awards_page(self):
        response = self.client.get(reverse('contract_awards_list_view'))

        if "login" in response.url:
            login_status = self.client.login(
                username="testuser", password="12345"
            )
            self.assertEqual(login_status, True)

        response = self.client.get(reverse('contract_awards_list_view'))
        winners = response.context["winners"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0].tender.title, self.winner.tender.title)
        self.assertEqual(winners[0].vendor, self.winner.vendor)
        self.assertEqual(winners[0].currency, self.winner.currency)
