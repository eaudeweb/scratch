from django.core import mail
from django.test import TestCase
from app.models import Notification
from django.template.loader import render_to_string
from django.conf import settings
from app.management.commands.notify import build_email
from django.core import management
from app.factories import TenderFactory, NotificationFactory


class SendMailTest(TestCase):
    def setUp(self):
        self.tender1 = TenderFactory(
            title="test_title1",
            url="https://www.ungm.org/Public/Notice/94909",
            favourite=True,
        )

        self.tender2 = TenderFactory(
            title="test_title2", url="https://www.ungm.org/Public/Notice/94920"
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
                "tenders": [self.tender1, self.tender2],
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

        self.assertEqual(self.tender1.organization in alt_body, True)
        self.assertEqual(self.tender2.organization in alt_body, True)

    def test_mailing_favorites(self):
        management.call_command("notify_favorites")
        self.assertEqual(len(mail.outbox), 1)

        self.tender1.organization = "CHANGE1"
        self.tender1.save()

        management.call_command("notify_favorites")
        self.assertEqual(len(mail.outbox), 2)

        self.tender2.organization = "CHANGE2"
        self.tender2.save()

        management.call_command("notify_favorites")
        self.assertEqual(len(mail.outbox), 2)

        message = mail.outbox[0].alternatives[0][0]
        self.assertEqual("Favorite tender(s) update" in message, True)
        self.assertEqual(self.tender1.organization in message, False)
        self.assertEqual(self.tender2.organization in message, False)
