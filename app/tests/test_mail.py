from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from django.conf import settings
from django.core import mail, management
from django.template.loader import render_to_string
from django.utils import timezone

from app.factories import TenderFactory, NotificationFactory, KeywordFactory
from app.management.commands.notify import build_email
from app.models import Notification, Tender
from app.tests.base import BaseTestCase


class SendMailTest(BaseTestCase):
    def setUp(self):
        super(SendMailTest, self).setUp()
        self.keyword = KeywordFactory()
        self.tender1 = TenderFactory(
            reference="RFQ 47-2019",
            title="test_title1",
            url="https://www.ungm.org/Public/Notice/94909",
            favourite=True,
            published=datetime.now(timezone.utc) - timedelta(days=2),
            deadline=datetime.now(timezone.utc) + timedelta(days=3) - timedelta(hours=1),
        )

        self.tender2 = TenderFactory(
            reference="2019/FLCHI/FLCHI/102665",
            title="test_title2 python",
            url="https://www.ungm.org/Public/Notice/94920",
            published=datetime.now(timezone.utc) - timedelta(days=3),
            deadline=datetime.now(timezone.utc) + timedelta(days=7) - timedelta(hours=1),
        )

        self.tender3 = TenderFactory(
            reference="RFP 56956",
            title="test_title3",
            url="https://www.ungm.org/Public/Notice/92850",
            published=datetime.now(timezone.utc) - timedelta(days=1),
            deadline=datetime.now(timezone.utc) + timedelta(days=1) - timedelta(hours=1),
        )

        self.notified_user1 = NotificationFactory()
        self.notified_user2 = NotificationFactory()

    def test_mailing(self):
        subject = "New tenders available"
        notifications = Notification.objects.all()
        recipients = [notification.email for notification in notifications]

        html_content = render_to_string(
            "mails/new_tenders.html",
            {
                "tenders": [self.tender1, self.tender2, self.tender3],
                "domain": settings.BASE_URL,
            },
        )

        email = build_email(subject, recipients, None, html_content)
        email.send()

        self.assertEqual(len(mail.outbox), 1)

        body = mail.outbox[0].body
        alt_body = mail.outbox[0].alternatives[0][0]

        self.assertEqual(self.tender1.title in body, True)
        self.assertEqual(self.tender2.title in body, True)
        self.assertEqual(self.tender3.title in body, True)

        self.assertEqual(self.tender1.organization in alt_body, True)
        self.assertEqual(self.tender2.organization in alt_body, True)
        self.assertEqual(self.tender3.organization in alt_body, True)

    def test_notify(self):
        management.call_command("notify")
        self.assertEqual(len(mail.outbox), 3)

        mail1 = mail.outbox[0].alternatives[0][0]
        mail2 = mail.outbox[1].alternatives[0][0]
        mail3 = mail.outbox[2].alternatives[0][0]

        self.assertEqual(self.tender3.title in mail1, True)
        self.assertEqual(self.tender1.title in mail2, True)
        self.assertEqual(self.tender2.title in mail3, True)

    def test_notify_digest(self):
        management.call_command("notify", digest=True)
        self.assertEqual(len(mail.outbox), 1)

        alt_body = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(alt_body, "html.parser")

        tender_list = soup.find("ol", {"class": "tender-list"}).find_all("a")
        self.assertEqual(len(tender_list), 3)
        self.assertEqual(tender_list[0]["href"], self.tender3.url)
        self.assertEqual(tender_list[1]["href"], self.tender1.url)
        self.assertEqual(tender_list[2]["href"], self.tender2.url)

    def test_mailing_favorites(self):
        original_tender1_organization = self.tender1.organization
        management.call_command("notify_favorites")
        self.assertEqual(len(mail.outbox), 1)

        self.tender1 = Tender.objects.get(reference=self.tender1.reference)
        self.tender1.organization = "CHANGE1"
        self.tender1.save()

        management.call_command("notify_favorites")
        self.assertEqual(len(mail.outbox), 2)

        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.tender3.organization = "CHANGE2"
        self.tender3.save()

        management.call_command("notify_favorites")
        self.assertEqual(len(mail.outbox), 2)

        message = mail.outbox[0].alternatives[0][0]
        self.tender1 = Tender.objects.get(reference=self.tender1.reference)
        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.assertEqual("Favorite tender(s) update" in message, True)
        self.assertEqual(original_tender1_organization in message, False)
        self.assertEqual(self.tender1.organization in message, True)
        self.assertEqual(self.tender3.organization in message, False)

    def test_mailing_favorites_digest(self):
        self.tender2 = Tender.objects.get(reference=self.tender2.reference)
        self.tender2.organization = "CHANGE2"
        self.tender2.favourite = True
        self.tender2.save()

        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.tender3.organization = "CHANGE3"
        self.tender3.favourite = True
        self.tender3.save()

        management.call_command("notify_favorites", digest=True)
        self.assertEqual(len(mail.outbox), 1)

        alt_body = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(alt_body, "html.parser")

        tender_list = soup.find("ol", {"class": "tender-list"}).find_all("a")
        self.assertEqual(len(tender_list), 3)
        self.assertEqual(tender_list[0]["href"], self.tender3.url)
        self.assertEqual(tender_list[1]["href"], self.tender1.url)
        self.assertEqual(tender_list[2]["href"], self.tender2.url)

    def test_mailing_keywords(self):
        management.call_command("notify_keywords")
        self.assertEqual(len(mail.outbox), 1)

        self.tender2.organization = "CHANGE1"
        self.tender2.save()

        management.call_command("notify_keywords")
        self.assertEqual(len(mail.outbox), 2)

        self.tender3.organization = "CHANGE2"
        self.tender3.save()

        management.call_command("notify_keywords")
        self.assertEqual(len(mail.outbox), 2)

        message = mail.outbox[0].alternatives[0][0]
        self.assertEqual("Keyword tender(s) update" in message, True)
        self.assertEqual(self.tender2.organization in message, False)
        self.assertEqual(self.tender3.organization in message, False)

    def test_mailing_keywords_digest(self):
        self.tender1 = Tender.objects.get(reference=self.tender1.reference)
        self.tender1.title = "test_title1 python"
        self.tender1.save()

        self.tender2 = Tender.objects.get(reference=self.tender2.reference)
        self.tender2.title = "test_title2 changed python"
        self.tender2.save()

        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.tender3.title = "test_title3 python"
        self.tender3.save()

        management.call_command("notify_keywords", digest=True)
        self.assertEqual(len(mail.outbox), 1)

        alt_body = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(alt_body, "html.parser")

        tender_list = soup.find("ol", {"class": "tender-list"}).find_all("a")
        self.assertEqual(len(tender_list), 3)
        self.assertEqual(tender_list[0]["href"], self.tender3.url)
        self.assertEqual(tender_list[1]["href"], self.tender1.url)
        self.assertEqual(tender_list[2]["href"], self.tender2.url)

    def test_deadline_notification(self):
        self.tender2 = Tender.objects.get(reference=self.tender2.reference)
        self.tender2.favourite = True
        self.tender2.save()

        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.tender3.favourite = True
        self.tender3.save()

        management.call_command("deadline_notifications")
        self.assertEqual(len(mail.outbox), 3)

        mail1 = mail.outbox[0].alternatives[0][0]
        mail2 = mail.outbox[1].alternatives[0][0]
        mail3 = mail.outbox[2].alternatives[0][0]

        self.assertEqual(self.tender3.url in mail1, True)
        self.assertEqual(self.tender1.url in mail2, True)
        self.assertEqual(self.tender2.url in mail3, True)
