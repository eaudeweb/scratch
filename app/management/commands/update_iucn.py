from django.db.models import Q

from app.models import Tender
from datetime import datetime, timedelta
from app.parsers.iucn import IUCNWorker
from django.core.management.base import BaseCommand, CommandError
from app.management.commands.base.params import BaseParamsUI
from app.notifications import send_error_email
from app.utils import log_tenders_update, TenderSource


class Command(BaseCommand, BaseParamsUI):
    help = 'Gets all IUCN tenders from the past n days'

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
        self.stdout.write(
            self.style.SUCCESS('Importing new IUCN tenders...')
        )
        old_tender_count = Tender.objects.filter(source="IUCN").count()
        if kwargs['days_ago']:
            days_ago = kwargs['days_ago']
            last_date = datetime.today() - timedelta(days=days_ago)
        elif not old_tender_count:
            raise CommandError(
                "The database is empty, argument --days_ago is missing"
            )
        else:
            last_date = datetime.combine(Tender.objects.filter(~Q(published=None), Q(source='IUCN')).latest('published').published, datetime.min.time())

        try:
            w = IUCNWorker()
            w.parse_latest_notices(last_date)
            tenders_imported = Tender.objects.filter(source="IUCN").count() - old_tender_count
            IUCNWorker.add_worker_log(tenders_imported)
            success_msg = f'{tenders_imported} new IUCN tender(s) imported'
            self.stdout.write(
                self.style.SUCCESS(success_msg)
            )
            return success_msg
        except Exception as error:
            self.stdout.write(
                self.style.ERROR('IUCN tenders update failed: {}'.format(error))
            )
            send_error_email(str(error))
            raise

    def add_arguments(self, parser):
        parser.add_argument(
            '--days_ago',
            help='Get tenders published n days ago',
            type=int,
        )