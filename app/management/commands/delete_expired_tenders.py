from django.core.management.base import BaseCommand, CommandError
from app.models import Tender
from django.conf import settings
from datetime import datetime, timezone
from app.management.commands.base.params import BaseParamsUI


class Command(BaseCommand, BaseParamsUI):
    help = "Deletes tenders that are past due"

    def handle(self, *args, **options):
        current_time = datetime.now(timezone.utc)
        tenders = Tender.objects.all()

        for tender in tenders:
            time_diff = tender.deadline - current_time
            days = time_diff.days
            if int(days) < 0 and abs(days) >= settings.DELETE_EXPIRED_DAYS:
                tender.delete()

        return self.stdout.write(self.style.SUCCESS('Tenders older than %d days deleted'
                                                    % settings.DELETE_EXPIRED_DAYS))
