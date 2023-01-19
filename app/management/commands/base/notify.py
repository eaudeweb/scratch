from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from getenv import env

from app.notifications import build_email
from app.models import Tender, SOURCE_CHOICES
from app.parsers.ted import TEDWorker
from app.parsers.ungm import UNGMWorker
from app.management.commands.base.params import BaseParamsUI
from app.utils import emails_to_notify

ENDPOINT_URI = 'https://www.ungm.org'

User = get_user_model()


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
        # TODO: Investigate why this is not printed to the console in the case
        # of notify_keywords
        self.stdout.write(
            self.style.SUCCESS(
                f'Sending notifications about {self.notification_type()} '
                f'tender updates...'
            )
        )
        self.options = options
        digest = options['digest']
        changed_tenders = self.scrape_tenders()

        if changed_tenders:
            self.send_update_email(
                changed_tenders, digest, self.notification_type())

        return self.style.SUCCESS(
            f'Sent notifications about {changed_tenders.count()} tender(s).'
        )

    def add_arguments(self, parser):
        parser.add_argument(
            '--digest',
            action='store_true',
            help='If set, all tenders will be notified in one email.'
        )

    def get_recipients(self):
        user_id = self.options.get("user_id")
        if user_id:
            return [User.objects.get(id=user_id).email]
        return emails_to_notify()

    def send_update_email(self, tenders, digest, notification_type):
        s = 's' if digest else ''
        subject = f'{notification_type} tender{s} Update'
        recipients = self.get_recipients()

        if digest:
            html_content = render_to_string(
                'mails/tender_update.html',
                {
                    'tenders': tenders,
                    'domain': settings.BASE_URL,
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
                        'domain': settings.BASE_URL,
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
            self.stdout.write(
                self.style.SUCCESS(
                    f'Scraping {ted_tenders.count()} TED tenders...'
                )
            )
            w = TEDWorker()
            w.ftp_download_tender_archive(ted_tenders)
            changed_ted_tenders, _ = w.parse_notices(ted_tenders)

        changed_ungm_tenders = []
        if ungm_tenders.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f'Scraping {ungm_tenders.count()} UNGM tenders...'
                )
            )
            w = UNGMWorker()
            changed_ungm_tenders, _ = w.parse_tenders(ungm_tenders)
        return Tender.objects.filter(
            reference__in=[
                t[0]['reference']
                for t in changed_ted_tenders + changed_ungm_tenders
            ]
        )
