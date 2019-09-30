from django.conf import settings
from django.core import mail, management
from django.template.loader import render_to_string

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
        )

        self.tender2 = TenderFactory(
            reference="2019/FLCHI/FLCHI/102665",
            title="test_title2 python",
            url="https://www.ungm.org/Public/Notice/94920",
        )

        self.tender3 = TenderFactory(
            reference="RFP 56956",
            title="test_title3",
            url="https://www.ungm.org/Public/Notice/92850",
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
