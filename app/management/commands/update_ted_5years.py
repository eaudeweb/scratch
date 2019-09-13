import logging
from datetime import datetime, date
from app.parsers.ted import TEDWorker
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: %(message)s')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            help='Get tenders published from a given date (default is 5 years ago)',
            type=str,
        )

    def handle(self, *args, **options):

        given_date = None
        now = date.today()
        default = now - relativedelta(years=5)

        try:
            given_date = datetime.strptime(options['date'], '%d/%m/%Y').date()
        except TypeError:
            logger.warning('No date was provived or it was provided but does not match the format (e.g. 19/05/2017)')
            logger.warning('Default value of 5 years ago is chosen')

        try:
            w = TEDWorker(given_date or default)
            w.ftp_download_latest_archives()
            w.parse_notices()
        except Exception as e:
            logging.critical(e)

        self.stdout.write(self.style.SUCCESS(f"TED tenders updated (since {options['date'] or default})"))
        return f"TED tenders updated (since {options['date'] or default})"
