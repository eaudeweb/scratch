from django.contrib.auth.models import User
from django.urls import reverse

from app.factories import TenderFactory, AwardFactory, VendorFactory
from app.tests.base import BaseTestCase


class AwardsViewTest(BaseTestCase):
    def setUp(self):
        super(AwardsViewTest, self).setUp()
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()

        vendor = VendorFactory(name="test_vendor")
        self.tender = TenderFactory(title="test_title")
        self.award = AwardFactory(tender=self.tender)
        self.award.vendors.add(vendor)

    def test_awards_page(self):
        response = self.client.get(reverse('contract_awards_list_view'))

        if "login" in response.url:
            login_status = self.client.login(
                username="testuser", password="12345"
            )
            self.assertEqual(login_status, True)

        response = self.client.get(reverse('contract_awards_list_view'))
        awards = response.context["awards"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(awards), 1)
        self.assertEqual(awards[0].tender.title, self.award.tender.title)
        self.assertEqual(awards[0].vendors.first(), self.award.vendors.all().first())
        self.assertEqual(awards[0].currency, self.award.currency)
