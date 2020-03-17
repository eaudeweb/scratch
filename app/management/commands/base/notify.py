from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from getenv import env

from app.notifications import build_email
from app.models import Tender, EmailAddress, SOURCE_CHOICES
from app.parsers.ted import TEDWorker
from app.parsers.ungm import UNGMWorker
from app.management.commands.base.params import BaseParamsUI

ENDPOINT_URI = 'https://www.ungm.org'


class BaseNotifyCommand(BaseCommand, BaseParamsUI):
    @staticmethod
    def get_parameters():
        return [
            {
                'name': 'digest',
                'display': 'Digest',
                'type': 'checkbox',
            },
        ]

    @property
    def notification_type(self):
        raise NotImplementedError(
            'subclasses of BaseNotifyCommand must provide a notification_type '
            'member'
        )

    def get_tenders(self):
        raise NotImplementedError(
            'subclasses of BaseNotifyCommand must provide a get_tenders() '
            'method'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                f'Sending notifications about {self.notification_type()} '
                f'tender updates...'
            )
        )
        digest = options['digest']
        changed_tenders = self.scrape_tenders()

        if changed_tenders:
            BaseNotifyCommand.send_update_email(
                changed_tenders, digest, self.notification_type())
        self.stdout.write(
            self.style.SUCCESS(
                f'Sent notifications about {changed_tenders.count()} '
                f'tender(s).'
            )
        )

    def add_arguments(self, parser):
        parser.add_argument(
            '--digest',
            action='store_true',
            help='If set, all tenders will be notified in one email.'
        )

    @staticmethod
    def send_update_email(tenders, digest, notification_type):
        s = 's' if digest else ''
        subject = f'{notification_type} tender{s} Update'
        notifications = EmailAddress.objects.filter(notify=True)
        recipients = [notification.email for notification in notifications]

        if digest:
            html_content = render_to_string(
                'mails/tender_update.html',
                {
                    'tenders': tenders,
                    'domain': env('BASE_URL'),
                    'notification_type': notification_type
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

        else:
            for tender in tenders:
                html_content = render_to_string(
                    'mails/tender_update.html',
                    {
                        'tenders': [tender],
                        'domain': env('BASE_URL'),
                        'notification_type': notification_type
                    }
                )

                email = build_email(subject, recipients, None, html_content)
                email.send()

        tenders.update(notified=True)

    def scrape_tenders(self):
        """
        Downloads new tender data and scrape it, using the information to
        update existing tenders. New tenders are not created. This is done to
        make sure we are notifying the users only about the latest information.
        """
        tenders = self.get_tenders()

        ted_tenders = tenders.filter(source=dict(SOURCE_CHOICES).get('TED'))
        ungm_tenders = tenders.filter(source=dict(SOURCE_CHOICES).get('UNGM'))

        changed_ted_tenders = []
        if ted_tenders.exists():
            w = TEDWorker()
            w.ftp_download_tender_archive(ted_tenders)
            changed_ted_tenders, _ = w.parse_notices(ted_tenders)

        changed_ungm_tenders = []
        if ungm_tenders.exists():
            w = UNGMWorker()
            changed_ungm_tenders, _ = w.parse_tenders(ungm_tenders)
        return Tender.objects.filter(
            reference__in=[
                t[0]['reference']
                for t in changed_ted_tenders + changed_ungm_tenders
            ]
        )
