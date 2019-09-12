from app.models import Tender
from app.parsers.ungm import UNGMWorker
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
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

        w = UNGMWorker()
        w.parse_latest_notices(last_date)

        self.stdout.write(self.style.SUCCESS('UNGM tenders updated'))

    def add_arguments(self, parser):
        parser.add_argument(
            '--days_ago',
            help='Get tenders published n days ago',
            type=int,
        )
