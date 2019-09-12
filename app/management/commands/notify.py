from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from app.models import Tender, Notification, Email, Winner, set_notified
from django.conf import settings
from getenv import env
from app.management.commands.base.params import BaseParamsUI


class Command(BaseCommand, BaseParamsUI):
    help = 'Notifies all users about new available tenders'

    @staticmethod
    def get_parameters():
        return [
            {
                'name': 'digest',
                'display': 'Digest',
                'type': 'checkbox',
            },
        ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--digest',
            action='store_true',
            help='If set, all tenders will be notified in one email.'
        )

    def handle(self, *args, **options):
        digest = options['digest']
        tenders = Tender.objects.filter(notified=False)
        awards = Winner.objects.filter(notified=False)
        if (len(tenders) > 0) or (len(awards) > 0):
            send_email(tenders, awards, digest)


def send_email(tenders, awards, digest):
    subject = 'New tenders available' if digest else 'New tender available'
    notifications = Notification.objects.all()
    recipients = [notification.email for notification in notifications]
    title = ''

    if digest:
        if tenders:
            title += 'New Tenders'
            if awards:
                title += ' and '
        if awards:
            title += 'New Contract Awards'

        html_content = render_to_string(
            'mails/new_tenders.html',
            {
                'tenders': tenders,
                'awards': awards,
                'title': title,
                'domain': env('BASE_URL')
            }
        )

        email = build_email(subject, recipients, None, html_content)
        email.send()

        for tender in tenders:
            set_notified(tender)

        for award in awards:
            set_notified(award)

    else:
        title = 'New Tenders'
        for tender in tenders:
            html_content = render_to_string(
                'mails/new_tenders.html',
                {
                    'tenders': [tender],
                    'title': title,
                    'domain': env('BASE_URL')
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

            set_notified(tender)

        for award in awards:
            title = 'New Contract Awards'
            html_content = render_to_string(
                'mails/new_tenders.html',
                {
                    'awards': [award],
                    'title': title,
                    'domain': env('BASE_URL')
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

            set_notified(award)


def build_email(subject, recipients, cc, body):
    sender = settings.EMAIL_SENDER

    return Email(
        subject=subject,
        from_email=sender,
        to=recipients,
        cc=cc,
        body=body
    )
