from django.core import mail
from django.test import TestCase
from app.models import Tender, Notification
from django.template.loader import render_to_string
from django.conf import settings
from app.management.commands.notify import build_email
from django.utils import timezone
from datetime import datetime
from django.core import management


class SendMailTest(TestCase):
    def setUp(self):
        self.tender1 = Tender.objects.create(
            title="test_title1",
            organization='UNGM',
            published=datetime.now(timezone.utc),
            deadline=datetime.now(timezone.utc),
            reference="RFC/TEST/123",
            url="https://www.ungm.org/Public/Notice/94909",
            source="UNGM",
            unspsc_codes="98765",
            favourite=True
        )

        self.tender2 = Tender.objects.create(
            title="test_title2",
            organization='TED',
            published=datetime.now(timezone.utc),
            deadline=datetime.now(timezone.utc),
            reference="RFC/TEST/1234",
            url="https://www.ungm.org/Public/Notice/94920",
            source="UNGM",
            unspsc_codes="98760",
        )

        self.notified_user1 = Notification.objects.create(email='test01@test.test')
        self.notified_user2 = Notification.objects.create(email='test02@test.test')

    def test_mailing(self):
        subject = 'New tenders available'
        notifications = Notification.objects.all()
        recipients = [notification.email for notification in notifications]

        html_content = render_to_string(
            'mails/new_tenders.html',
            {
                'tenders': [self.tender1, self.tender2],
                'domain': settings.BASE_URL
            }
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
        management.call_command('notify_favorites')
        self.assertEqual(len(mail.outbox), 1)

        self.tender1.organization = "CHANGE1"
        self.tender1.save()

        management.call_command('notify_favorites')
        self.assertEqual(len(mail.outbox), 2)

        self.tender2.organization = "CHANGE2"
        self.tender2.save()

        management.call_command('notify_favorites')
        self.assertEqual(len(mail.outbox), 2)

        message = mail.outbox[0].alternatives[0][0]
        self.assertEqual('Favorite tender(s) update' in message, True)
        self.assertEqual(self.tender1.organization in message, False)
        self.assertEqual(self.tender2.organization in message, False)
