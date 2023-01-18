from django.core.management.base import BaseCommand
from app.models import Tender
from app.management.commands.base.params import BaseParamsUI
from app.notifications import send_tenders_email


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
        self.stdout.write(
            self.style.SUCCESS('Sending notifications about new tenders...')
        )
        digest = options['digest']
        tenders = Tender.objects.filter(
            notified=False, awards__isnull=True).order_by('-published')
        tender_count = tenders.count()
        if tender_count:
            send_tenders_email(tenders, digest)

        return self.style.SUCCESS(
            f'Sent notifications about {tender_count} tenders...'
        )
