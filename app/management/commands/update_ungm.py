from app.models import Tender
from datetime import datetime, timedelta
from app.parsers.ungm import UNGMWorker
from django.core.management.base import BaseCommand, CommandError
from app.management.commands.base.params import BaseParamsUI
from app.notifications import send_error_email

ENDPOINT_URI = 'https://www.ungm.org'


class Command(BaseCommand, BaseParamsUI):
    help = 'Gets all UNGM tenders from the past n days'

    @staticmethod
    def get_parameters():
        return [
            {
                'name': 'days_ago',
                'display': 'Days ago',
                'type': 'text',
            },
        ]

    def handle(self, *args, **kwargs):

        if kwargs['days_ago']:
            days_ago = kwargs['days_ago']
            last_date = (datetime.today() - timedelta(days=days_ago)).date()
        elif not Tender.objects.all():
            raise CommandError(
                "The database is empty, argument --days_ago is missing"
            )
        else:
            last_date = Tender.objects.latest('published').published

        try:
            w = UNGMWorker()
            w.parse_latest_notices(last_date)

            self.stdout.write(self.style.SUCCESS('UNGM tenders updated'))
            return 'UNGM tenders updated'
        except Exception as error:
            self.stdout.write(
                self.style.ERROR('TED tenders update failed: {}'.format(error))
            )
            send_error_email(str(error))

    def add_arguments(self, parser):
        parser.add_argument(
            '--days_ago',
            help='Get tenders published n days ago',
            type=int,
        )
