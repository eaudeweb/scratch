from datetime import date, timedelta
from django.core.management.base import BaseCommand

from app.management.commands.base.params import BaseParamsUI
from app.parsers.ted import TEDWorker
from app.notifications import send_error_email


class Command(BaseCommand, BaseParamsUI):
    help = 'Gets all TED tenders from the past n days'

    @staticmethod
    def get_parameters():
        return [
            {
                'name': 'days_ago',
                'display': 'Days ago',
                'type': 'text',
            },
        ]

    @staticmethod
    def days_ago(days):
        if days:
            return date.today() - timedelta(days=days)
        return None

    def add_arguments(self, parser):
        parser.add_argument(
            '--days_ago',
            help='Get tenders published n days ago',
            type=int,
        )

    def handle(self, *args, **options):
        try:
            last_ted_update = Command.days_ago(int(options['days_ago']))
        except TypeError:
            last_ted_update = None

        try:
            w = TEDWorker(last_ted_update)
            w.ftp_download_latest_archives()
            changed_tenders, tenders_count = w.parse_notices()
            w.add_worker_log("TED", tenders_count)
            self.stdout.write(self.style.SUCCESS('TED tenders updated'))
            return "TED tenders updated"
        except Exception as error:
            self.stdout.write(
                self.style.ERROR('TED tenders update failed: {}'.format(error))
            )
            send_error_email(str(error))
