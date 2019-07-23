from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from app.models import Tender, Notification, Email, set_notified
from django.conf import settings


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--digest',
            action='store_true',
            help='If set, all tenders will be notified in one email.'
        )

    def handle(self, *args, **options):
        digest = options['digest']
        tenders = Tender.objects.filter(notified=False)

        if tenders:
            send_email(tenders, digest)


def send_email(tenders, digest):
    subject = 'New tenders available' if digest else 'New tender available'
    notifications = Notification.objects.all()
    recipients = [notification.email for notification in notifications]

    if digest:
        html_content = render_to_string(
            'mails/new_tenders.html',
            {
                'tenders': tenders,
                'domain': settings.BASE_URL
            }
        )

        email = build_email(subject, recipients, None, html_content)
        email.send()

        for tender in tenders:
            set_notified(tender)

    else:
        for tender in tenders:
            html_content = render_to_string(
                'mails/new_tenders.html',
                {
                    'tenders': [tender],
                    'domain': settings.BASE_URL
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

            set_notified(tender)


def build_email(subject, recipients, cc, body):
    sender = 'Eau de Web <Tenders Bot>'

    return Email(
        subject=subject,
        from_email=sender,
        to=recipients,
        cc=cc,
        body=body
    )
