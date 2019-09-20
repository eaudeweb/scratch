from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from getenv import env

from app.management.commands.notify import build_email
from app.models import Notification, SOURCE_CHOICES
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
        raise NotImplementedError('subclasses of BaseNotifyCommand must provide a notification_type member')

    def get_tenders(self):
        raise NotImplementedError('subclasses of BaseNotifyCommand must provide a get_tenders() method')

    def handle(self, *args, **options):
        digest = options['digest']
        changed_tenders = self.scrap_tenders()

        if changed_tenders:
            BaseNotifyCommand.send_update_email(changed_tenders, digest, self.notification_type())

    def add_arguments(self, parser):
        parser.add_argument(
            '--digest',
            action='store_true',
            help='If set, all tenders will be notified in one email.'
        )

    @staticmethod
    def send_update_email(tenders, digest, notification_type):
        subject = f'{notification_type} tenders Update' if digest else f'{notification_type} tender Update'
        notifications = Notification.objects.all()
        recipients = [notification.email for notification in notifications]
        tends = [tx[0] for tx in tenders]

        if digest:
            html_content = render_to_string(
                'mails/tender_update.html',
                {
                    'tenders': tends,
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
                        'tenders': [tender[0]],
                        'domain': env('BASE_URL'),
                        'notification_type': notification_type
                    }
                )

                email = build_email(subject, recipients, None, html_content)
                email.send()

    def scrap_tenders(self):
        tenders = self.get_tenders()

        ungm_tenders = []
        ted_tenders = []
        for tender in tenders:
            if tender.source == dict(SOURCE_CHOICES).get('TED'):
                ted_tenders.append(tender)
            else:
                ungm_tenders.append(tender)

        changed_ted_tenders = []
        if len(ted_tenders):
            w = TEDWorker()
            w.ftp_download_tender_archive(ted_tenders)
            changed_ted_tenders = w.parse_notices(ted_tenders)

        changed_ungm_tenders = []
        if len(ungm_tenders):
            w = UNGMWorker()
            changed_ungm_tenders = w.parse_tenders(ungm_tenders)

        return changed_ted_tenders + changed_ungm_tenders
