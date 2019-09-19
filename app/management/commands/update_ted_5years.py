import logging
from datetime import datetime, date, timedelta

from django.utils.timezone import make_aware
from django_q.tasks import async_task

from app.models import Task
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
        now = date.today()
        default = now - relativedelta(years=5)

        try:
            given_date = datetime.strptime(options['date'], '%d/%m/%Y').date()
        except TypeError:
            given_date = default
            logger.warning('No date was provived or it was provided but does not match the format (e.g. 19/05/2017)')
            logger.warning('Default value of 5 years ago is chosen')

        try:
            today = date.today()

            command_name = "update_ted_5years"
            command = 'app.parsers.ted.process_daily_archive'

            while given_date < today:
                task_id = async_task(command, given_date)

                t = Task(
                    id=task_id,
                    args=command_name,
                    kwargs=f'given_date: {given_date}',
                    started=make_aware(datetime.now()),
                )
                t.save()

                given_date = given_date + timedelta(days=1)

        except Exception as e:
            logging.critical(e)

        return self.stdout.write(self.style.SUCCESS(f"Queued TED tenders updates (since {options['date'] or default})"))
