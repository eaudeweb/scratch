from django.core.management.base import BaseCommand, CommandError
from app.models import Winner


class Command(BaseCommand):
    def handle(self, *args, **options):
        winners = Winner.objects.all()

        for winner in winners:
            winner.vendor = winner.vendor.strip()
            winner.save()

        self.stdout.write(self.style.SUCCESS('Removed unnecessary new lines'))
