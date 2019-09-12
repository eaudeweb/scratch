from django.core.management.base import BaseCommand

from app.parsers.ted import TEDWorker


class Command(BaseCommand):
    def handle(self, *args, **options):
        w = TEDWorker()
        w.ftp_download_latest_archives()
        w.parse_notices()

        self.stdout.write(self.style.SUCCESS('TED tenders updated'))
