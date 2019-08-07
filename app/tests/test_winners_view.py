from django.test import TestCase
from app.models import Tender, Winner
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime


class WinnersViewTest(TestCase):
    def setUp(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()

        tender = Tender.objects.create(
            title="test_title",
            reference="RFC/TEST/123",
            url="http://test.com",
            source="UNGM",
            unspsc_codes="98765",
        )
        Winner.objects.create(
            vendor="test_vendor",
            currency="USD",
            award_date=datetime.now(timezone.utc),
            tender=tender
        )

    def test_awards_page(self):
        response = self.client.get("/app/awards/")

        if "login" in response.url:
            login_status = self.client.login(
                username="testuser", password="12345"
            )
            self.assertEqual(login_status, True)

        response = self.client.get("/app/awards/")
        winners = response.context["winners"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0].tender.title, "test_title")
        self.assertEqual(winners[0].vendor, "test_vendor")
        self.assertEqual(winners[0].currency, "USD")
