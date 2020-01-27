from django.core.management.base import BaseCommand
from app.models import Tender, Award
from app.management.commands.base.params import BaseParamsUI
from app.notifications import send_update_email


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
        tenders = Tender.objects.filter(notified=False).order_by('-published')
        awards = Award.objects.filter(notified=False).order_by('-award_date')
        if (len(tenders) > 0) or (len(awards) > 0):
            send_update_email(tenders, awards, digest)
