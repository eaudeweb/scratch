
from app.models import Tender
from datetime import datetime, timedelta
from app.parsers.ungm import UNGMWorker
from django.core.management.base import BaseCommand, CommandError
from app.management.commands.base.params import BaseParamsUI
from app.notifications import send_error_email
from app.utils import log_tenders_update, TenderSource

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

    @log_tenders_update(tender_source=TenderSource.UNGM)
    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.SUCCESS('Importing new UNGM tenders...')
        )
        old_tender_count = Tender.objects.count()
        if kwargs['days_ago']:
            days_ago = kwargs['days_ago']
            last_date = (datetime.today() - timedelta(days=days_ago)).date()
        elif not old_tender_count:
            raise CommandError(
                "The database is empty, argument --days_ago is missing"
            )
        else:
            last_date = Tender.objects.latest('published').published

        try:
            w = UNGMWorker()
            w.parse_latest_notices(last_date)
            tenders_imported = Tender.objects.count() - old_tender_count
            success_msg = f'{tenders_imported} new UNGM tender(s) imported'
            self.stdout.write(
                self.style.SUCCESS(success_msg)
            )
            return success_msg
        except Exception as error:
            self.stdout.write(
                self.style.ERROR('UNGM tenders update failed: {}'.format(error))
            )
            send_error_email(str(error))
            raise

    def add_arguments(self, parser):
        parser.add_argument(
            '--days_ago',
            help='Get tenders published n days ago',
            type=int,
        )
