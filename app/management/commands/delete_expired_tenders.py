from django.core.management.base import BaseCommand, CommandError
from app.models import Tender
from django.conf import settings
from datetime import datetime, timezone


class Command(BaseCommand):

    def handle(self, *args, **options):
        current_time = datetime.now(timezone.utc)
        tenders = Tender.objects.all()

        for tender in tenders:
            time_diff = tender.deadline - current_time
            days = time_diff.days
            if days < 0 and abs(days) >= int(settings.DELETE_EXPIRED_DAYS):
                tender.delete()

        return self.stdout.write(self.style.SUCCESS('Tenders expired for more than %d days deleted'
                                                    % settings.DELETE_EXPIRED_DAYS))
